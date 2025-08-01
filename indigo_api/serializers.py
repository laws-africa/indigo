import os.path
from collections import OrderedDict

import logging
import reversion
from actstream.signals import action
from allauth.account.utils import user_display
from django.conf import settings
from django.contrib.auth.models import User
from lxml import etree
from lxml.etree import LxmlError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from typing import List

from cobalt import StructuredDocument, FrbrUri
from cobalt.akn import AKN_NAMESPACES, DEFAULT_VERSION
from indigo_api.models import Document, Attachment, Annotation, DocumentActivity, Work, Amendment, Language, \
    PublicationDocument, Task, Commencement
from indigo_api.signals import document_published

log = logging.getLogger(__name__)


def user_display_name(user):
    if user.first_name:
        name = user.first_name
        if user.last_name:
            name += ' %s' % user.last_name
    else:
        name = user.username

    return name


class SerializedRelatedField(serializers.PrimaryKeyRelatedField):
    """ Related field that serializers the entirety of the related object.
    For updates, only the primary key field is considered, everything else is
    ignored.
    """
    serializer = None

    def __init__(self, serializer=None, *args, **kwargs):
        if serializer is not None:
            self.serializer = serializer
        assert self.serializer is not None, 'The `serializer` argument is required.'

        super(SerializedRelatedField, self).__init__(*args, **kwargs)

    def get_serializer(self):
        if isinstance(self.serializer, str):
            self.serializer = globals()[self.serializer]
        return self.serializer

    def use_pk_only_optimization(self):
        return False

    def to_internal_value(self, data):
        # support both a dict and passing in the primary key directly
        if isinstance(data, dict):
            data = data['id']
        return super(SerializedRelatedField, self).to_internal_value(data)

    def to_representation(self, value):
        context = {}
        context.update(self.context)
        context['depth'] = context.get('depth', 0) + 1
        # don't recurse
        if context['depth'] > 1:
            return {'id': value.pk}
        return self.get_serializer()(context=context).to_representation(value)

    def get_choices(self, cutoff=None):
        queryset = self.get_queryset()
        if queryset is None:
            # Ensure that field.choices returns something sensible
            # even when accessed with a read-only field.
            return {}

        if cutoff is not None:
            queryset = queryset[:cutoff]

        return OrderedDict([
            (
                item.pk,
                self.display_value(item)
            )
            for item in queryset
        ])


class AmendmentEventSerializer(serializers.Serializer):
    """ Serializer matching :class:`cobalt.AmendmentEvent`
    """

    date = serializers.DateField()
    """ Date that the amendment took place """
    amending_title = serializers.CharField()
    """ Title of amending document """
    amending_uri = serializers.CharField()
    """ FRBR URI of amending document """


class RepealSerializer(serializers.Serializer):
    """ Describes the repeal event for a work. """
    # Matches :class:`cobalt.RepealEvent`

    date = serializers.DateField(help_text="Effective date of the repeal.")
    repealing_title = serializers.CharField(help_text="Title of the repealing work.")
    repealing_uri = serializers.CharField(help_text="FRBR URI of the repealing work.")


class AttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, write_only=True)
    filename = serializers.CharField(max_length=255, required=False)
    url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    view_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = (
            'id',
            'url', 'download_url', 'view_url',
            'file',
            'filename',
            'mime_type',
            'size',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at', 'mime_type', 'size')

    def get_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-attachments-detail', request=self.context['request'], kwargs={
            'document_id': instance.document_id,
            'pk': instance.pk,
        })

    def get_download_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-attachments-download', request=self.context['request'], kwargs={
            'document_id': instance.document_id,
            'pk': instance.pk,
        })

    def get_view_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-attachments-view', request=self.context['request'], kwargs={
            'document_id': instance.document_id,
            'pk': instance.pk,
        })

    def create(self, validated_data):
        file = validated_data.get('file', None)
        if not file:
            raise ValidationError({'file': "No file was submitted."})

        args = {}
        args.update(validated_data)
        args['size'] = file.size
        args['mime_type'] = file.content_type
        args['filename'] = args.get('filename', os.path.basename(file.name))
        args['document'] = args.get('document', self.context['document'])

        return super(AttachmentSerializer, self).create(args)

    def update(self, instance, validated_data):
        if 'file' in validated_data:
            raise ValidationError("Value of 'file' cannot be updated. Delete and re-create this attachment.")
        return super(AttachmentSerializer, self).update(instance, validated_data)

    def validate_filename(self, fname):
        return fname.replace('/', '')


class PublicationDocumentSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PublicationDocument
        fields = ('url', 'filename', 'mime_type', 'size', 'trusted_url')
        read_only_fields = fields

    def get_url(self, instance):
        if instance.trusted_url:
            return instance.trusted_url
        # HACK HACK HACK
        # TODO: this is a hack until we can teach indigo to be aware that
        #  the API might live on a different host
        return settings.INDIGO_URL + '/works{}/media/publication/{}'.format(
            instance.work.frbr_uri, instance.filename
        )


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'display_name', 'username')
        read_only_fields = fields

    def get_display_name(self, user):
        return user_display(user)


class VersionSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source='revision.date_created')
    comment = serializers.CharField(source='revision.comment')
    user = UserSerializer(source='revision.user')

    class Meta:
        model = reversion.models.Version
        fields = ('id', 'date', 'comment', 'user')
        read_only_fields = fields


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    content = serializers.CharField(required=False, write_only=True)
    """ A write-only field for setting the entire XML content of the document. """

    frbr_uri = serializers.CharField(read_only=True, help_text="FRBR URI that uniquely identifies this work.")

    links = serializers.SerializerMethodField(help_text="A list of alternate links for this document.")

    draft = serializers.BooleanField(default=True)
    language = serializers.CharField(source='language.code', required=True,
                                     help_text="Three letter ISO-639-2 language code for this work expression.")
    expression_frbr_uri = serializers.CharField(read_only=True,
                                                help_text="FRBR URI that uniquely identifies this work expression.")

    # if a title isn't given, it's taken from the associated work
    title = serializers.CharField(required=False, allow_blank=False, allow_null=False,
                                  help_text="Short title of the work, in the expression language.")

    # taken from the work
    publication_name = serializers.CharField(
        read_only=True, help_text="Name of the publication in which the work was originally published.")
    publication_number = serializers.CharField(
        read_only=True, help_text="Number of the publication in which the work was originally published.")
    publication_date = serializers.DateField(read_only=True, help_text="Date of original publication of the work.")
    commencement_date = serializers.DateField(read_only=True, help_text="Date on which the bulk of the work commences.")
    commencement_note = serializers.CharField(read_only=True,
                                              help_text="Additional information about the commencement.")
    assent_date = serializers.DateField(read_only=True, help_text="Date when the work was assented to.")
    numbered_title = serializers.CharField(
        read_only=True, source='work.numbered_title',
        help_text="Alternative title for the work, using the document type and number.")
    type_name = serializers.CharField(read_only=True, source='work.friendly_type',
                                      help_text="Human-friendly version of doctype and/or subtype.")

    amendments = AmendmentEventSerializer(
        many=True, read_only=True, source='amendment_events',
        help_text="List of amendments that have been applied to create this expression of the work.")

    repeal = RepealSerializer(read_only=True,
                              help_text="Description of the repeal of this work, if it has been repealed.")

    # only for provision editing
    provision_eid = serializers.CharField(required=False, allow_blank=True)

    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)

    class Meta:
        model = Document
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'content', 'title', 'draft',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'date', 'actor', 'number', 'frbr_uri', 'expression_frbr_uri',

            'publication_date', 'publication_name', 'publication_number',
            'expression_date', 'commencement_date', 'assent_date',
            'commencement_note',
            'language', 'amendments', 'repeal', 'numbered_title', 'type_name',

            'links',

            'provision_eid',
        )
        read_only_fields = ('country', 'locality', 'nature', 'subtype', 'date', 'actor', 'number', 'created_at', 'updated_at')

    def get_links(self, doc):
        return [
            {
                # A URL for the entire content of the document.
                # The content isn't included in the document description because it could be huge.
                "rel": "content",
                "title": "Content",
                "href": reverse('document-content', request=self.context['request'], kwargs={'pk': doc.pk}),
            },
            {
                "rel": "toc",
                "title": "Table of Contents",
                "href": reverse('document-toc', request=self.context['request'], kwargs={'pk': doc.pk}),
            },
            {
                "rel": "attachments",
                "title": "Attachments",
                "href": reverse('document-attachments-list', request=self.context['request'], kwargs={'document_id': doc.pk}),
            },
            {
                "rel": "annotations",
                "title": "Annotations",
                "href": reverse('document-annotations-list', request=self.context['request'], kwargs={'document_id': doc.pk}),
            },
        ]

    def validate(self, attrs):
        if attrs.get('content'):
            # validate the content
            try:
                frbr_uri = self.instance.work_uri
                doctype = frbr_uri.doctype if not attrs.get('provision_eid') else 'portion'
                doc = StructuredDocument.for_document_type(doctype)(attrs['content'])
            except (LxmlError, ValueError) as e:
                raise ValidationError("Invalid XML: %s" % str(e))

            # ensure the correct namespace
            if doc.namespace != AKN_NAMESPACES['3.0']:
                raise ValidationError(f"Document must have namespace {AKN_NAMESPACES['3.0']}, but it has {doc.namespace} instead.")

        return attrs

    def validate_frbr_uri(self, value):
        try:
            if not value:
                raise ValueError()
            return FrbrUri.parse(value.lower()).work_uri()
        except ValueError:
            raise ValidationError("Invalid FRBR URI: %s" % value)

    def validate_language(self, value):
        try:
            return Language.for_code(value)
        except Language.DoesNotExist:
            raise ValidationError("Invalid language: %s" % value)

    def create(self, validated_data):
        # cannot create a document using this serializer
        raise NotImplemented()

    def update(self, document, validated_data):
        """ Update and save document. """
        draft = document.draft

        self.update_document(document, validated_data)

        user = self.context['request'].user
        if user:
            document.updated_by_user = user
            if not document.created_by_user:
                document.created_by_user = user

        # save as a revision
        document.save_with_revision(user)

        # reload it to ensure we have an id for new documents
        document = Document.objects.get(pk=document.id)

        # signals
        if draft and not document.draft:
            action.send(user, verb='published', action_object=document,
                        place_code=document.work.place.place_code)
            document_published.send(sender=self.__class__, document=document, request=self.context['request'])
        elif not draft and document.draft:
            action.send(user, verb='unpublished', action_object=document,
                        place_code=document.work.place.place_code)

        return document

    def update_document(self, document, validated_data=None):
        """ Update document without saving it. """
        if validated_data is None:
            validated_data = self.validated_data

        # work around DRF stashing the language as a nested field
        if 'language' in validated_data:
            # this is really a Language object
            validated_data['language'] = validated_data['language']['code']

        # Document content must always come first so it can be overridden
        # by the other properties.
        content = validated_data.pop('content', None)
        provision_eid = validated_data.pop('provision_eid', None)
        if content is not None:
            if provision_eid:
                # this will reset the XML on the document
                document.update_provision_xml(provision_eid, content)
            else:
                document.reset_xml(content, from_model=True)

        # save rest of changes
        for attr, value in validated_data.items():
            setattr(document, attr, value)

        # Link to the appropriate work, based on the FRBR URI
        # Raises ValueError if the work doesn't exist
        document.work = Work.objects.get_for_frbr_uri(document.frbr_uri)
        document.copy_attributes()

        return document


class RenderSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /render API
    """
    document = DocumentSerializer()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].instance = self.instance


class ParseSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /parse API
    """
    content = serializers.CharField(write_only=True, required=False)
    fragment = serializers.CharField(write_only=True, required=False)
    id_prefix = serializers.CharField(write_only=True, required=False)


class DocumentAPISerializer(serializers.Serializer):
    """
    Helper to handle input documents for general document APIs
    """
    xml = serializers.CharField()
    language = serializers.CharField(min_length=3, max_length=3)
    provision_eid = serializers.CharField(allow_blank=True)
    element_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_xml(self, xml):
        """ mostly copied from DocumentSerializer.validate()
        """
        try:
            doctype = self.instance.work_uri.doctype if not self.initial_data.get('provision_eid') else 'portion'
            doc = StructuredDocument.for_document_type(doctype)(xml)
        except (LxmlError, ValueError) as e:
            raise ValidationError("Invalid XML: %s" % str(e))
        # ensure the correct namespace
        if doc.namespace != AKN_NAMESPACES[DEFAULT_VERSION]:
            raise ValidationError(
                f"Document must have namespace {AKN_NAMESPACES[DEFAULT_VERSION]}, but it has {doc.namespace} instead.")
        return xml

    def update_document(self):
        document = self.instance
        # the language could have been changed but not yet saved during editing, which might affect which plugin is used
        language_code = self.validated_data.get('language')
        if document.language.code != language_code:
            document.language = Language.for_code(language_code)
        # update the content with updated but unsaved changes too
        self.set_content()

    def set_content(self):
        document = self.instance
        xml = self.validated_data.get('xml')
        provision_eid = self.validated_data.get('provision_eid')
        if not provision_eid:
            # update the document's full XML with what's in the editor
            document.content = xml
        else:
            if self.use_full_xml:
                # we'll need the document's full XML for the analysis,
                # but update the relevant provision with what's in the editor first
                document.update_provision_xml(provision_eid, xml)
            else:
                # update the document to be a 'portion' and use only what's in the editor as the content
                document.work.work_uri.doctype = 'portion'
                document.content = xml

    def updated_xml(self):
        document = self.instance
        provision_eid = self.validated_data.get('provision_eid')
        if not provision_eid:
            # return the document's full updated XML
            return document.document_xml
        # otherwise, return only the provision being edited (NOT including the outer akn tag)
        # if we used the full XML for the analysis, grab only the appropriate provision as a portion
        xml = document.get_portion(provision_eid).main if self.use_full_xml else document.doc.portion
        return etree.tostring(xml, encoding='unicode')


class NoopSerializer(object):
    """
    Serializer that doesn't do any serializing, it just makes
    the data given to it to serialise available as +data+.
    """
    def __init__(self, instance, **kwargs):
        self.context = kwargs.pop('context', {})
        self.kwargs = kwargs
        self.data = instance


class AnnotationAnchorSerializer(serializers.Serializer):
    id = serializers.CharField()


class TaskSerializer(serializers.ModelSerializer):
    created_by_user = UserSerializer(read_only=True)
    updated_by_user = UserSerializer(read_only=True)
    country = serializers.CharField(source='country.code', default=None)
    locality = serializers.CharField(source='locality.code', default=None)
    work = serializers.CharField(allow_null=True, source='work.frbr_uri')
    annotation = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects, required=False, allow_null=True)
    assigned_to = UserSerializer(read_only=True)
    view_url = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'code',
            'description',
            'country',
            'locality',
            'work',
            'document',
            'state',
            'labels',
            'assigned_to',
            'annotation',
            'view_url',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',
        )
        read_only_fields = fields

    def get_view_url(self, instance):
        if not instance.pk:
            return None
        return reverse('task_detail', request=self.context['request'], kwargs={
            'place': instance.place.place_code,
            'pk': instance.pk,
        })


class AnnotationSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    created_by_user = UserSerializer(read_only=True)
    in_reply_to = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects, allow_null=True, required=False)
    task = TaskSerializer(read_only=True)

    class Meta:
        model = Annotation
        fields = (
            'id',
            'url',
            'text',
            'anchor_id',
            'in_reply_to',
            'closed',
            'task',
            'selectors',
            'created_by_user', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_by_user', 'in_reply_to', 'created_at', 'updated_at', 'task')

    def create(self, validated_data):
        validated_data['created_by_user'] = self.context['request'].user
        validated_data['document'] = self.context['document']
        return super(AnnotationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if 'in_reply_to' in validated_data:
            del validated_data['in_reply_to']
        return super(AnnotationSerializer, self).update(instance, validated_data)

    def validate_in_reply_to(self, in_reply_to):
        if in_reply_to:
            if in_reply_to.document_id != self.context['document'].id:
                raise ValidationError({'in_reply_to': "Annotation being replied to must be for the same document (%s)" % self.context['document'].id})
        return in_reply_to

    def get_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-annotations-detail', request=self.context['request'], kwargs={
            'document_id': instance.document_id,
            'pk': instance.pk,
        })


class DocumentActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    document_updated_at = serializers.SerializerMethodField()

    class Meta:
        model = DocumentActivity
        fields = (
            'user',
            'created_at',
            'updated_at',
            'nonce',
            'is_asleep',
            'document_updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {'nonce': {'required': True}}

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['document'] = self.context['document']
        return super(DocumentActivitySerializer, self).create(validated_data)

    def get_document_updated_at(self, obj):
        # load only the field we need
        doc = Document.objects.undeleted().only('updated_at').filter(pk=obj.document_id).first()
        return doc and doc.updated_at


class CommencementSerializer(serializers.ModelSerializer):
    """Details of a commencement event."""
    commencing_title = serializers.CharField(source="commencing_work.title", default=None,
                                             help_text="Title of the commencing work.")
    commencing_frbr_uri = serializers.CharField(source="commencing_work.frbr_uri", default=None,
                                                help_text="FRBR URI of the commencing work.")
    provisions = serializers.SerializerMethodField(
        help_text="A list of the element ids of the provisions that come into force with this commencement")

    class Meta:
        model = Commencement
        fields = (
            'commencing_title', 'commencing_frbr_uri',
            'date', 'main', 'all_provisions', 'provisions',
            'note',
        )
        read_only_fields = fields

    def get_provisions(self, instance) -> List[str]:
        return instance.provisions


class WorkSerializer(serializers.ModelSerializer):
    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)
    repealed_by = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')
    parent_work = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')
    commencing_work = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')
    commencement_date = serializers.DateField(required=False, allow_null=True)
    commencement_note = serializers.CharField(required=False, allow_null=True)
    country = serializers.CharField(source='country.code', required=True)
    locality = serializers.CharField(source='locality_code', required=False, allow_null=True)
    publication_document = PublicationDocumentSerializer(read_only=True)
    taxonomy_topics = serializers.SerializerMethodField()
    amendments_url = serializers.SerializerMethodField()
    """ URL of document amendments. """

    class Meta:
        model = Work
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'title', 'numbered_title',
            'publication_name', 'publication_number', 'publication_date', 'publication_document',
            'commenced', 'commencing_work', 'commencement_date', 'commencement_note',
            'assent_date', 'stub', 'principal',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',
            'parent_work', 'amendments_url',

            # repeal
            'repealed_date', 'repealed_by',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'date', 'actor', 'number', 'frbr_uri',

            # taxonomies
            'taxonomy_topics',
        )
        read_only_fields = fields

    def get_amendments_url(self, work):
        if not work.pk:
            return None
        return reverse('work-amendments-list', request=self.context['request'], kwargs={'work_id': work.pk})

    def get_taxonomy_topics(self, instance):
        return [t.slug for t in instance.public_taxonomy_topics()]


class WorkAmendmentSerializer(serializers.ModelSerializer):
    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)
    amending_work = SerializedRelatedField(queryset=Work.objects, required=True, allow_null=False, serializer=WorkSerializer)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Amendment
        fields = (
            # url is part of the rest framework
            'id', 'url',
            'amending_work', 'date',
            'updated_by_user', 'created_by_user',
            'created_at', 'updated_at',
        )
        read_only_fields = fields

    def get_url(self, instance):
        if not instance.pk:
            return None
        return reverse('work-amendments-detail', request=self.context['request'], kwargs={
            'work_id': instance.amended_work.pk,
            'pk': instance.pk,
        })
