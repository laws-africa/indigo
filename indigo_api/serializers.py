import logging
import os.path
from collections import OrderedDict
from lxml.etree import LxmlError

from django.db.models import Manager
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from taggit_serializer.serializers import TagListSerializerField
from cobalt import Act, FrbrUri
from cobalt.act import datestring
import reversion

from .models import Document, Attachment, Annotation, DocumentActivity, Work, Amendment
from .importers.registry import importers

log = logging.getLogger(__name__)


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
        if isinstance(self.serializer, basestring):
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
    """ Serializer matching :class:`cobalt.act.AmendmentEvent`
    """

    date = serializers.DateField()
    """ Date that the amendment took place """
    amending_title = serializers.CharField()
    """ Title of amending document """
    amending_uri = serializers.CharField()
    """ FRBR URI of amending document """


class RepealSerializer(serializers.Serializer):
    """ Serializer matching :class:`cobalt.act.RepealEvent`
    """

    date = serializers.DateField()
    """ Date that the repeal took place """
    repealing_title = serializers.CharField()
    """ Title of repealing document """
    repealing_uri = serializers.CharField()
    """ FRBR URI of repealing document """
    repealing_id = serializers.SerializerMethodField()
    """ ID of the repealing document, if available """

    def validate_empty_values(self, data):
        # we need to override this because for some reason the default
        # value given by DRF if this field isn't provided is {}, not None,
        # and we need to indicate that that is allowed.
        # see https://github.com/tomchristie/django-rest-framework/pull/2796
        if not data:
            return True, data
        return super(RepealSerializer, self).validate_empty_values(data)

    def get_repealing_id(self, instance):
        if hasattr(instance, 'repealing_document') and instance.repealing_document is not None:
            return instance.repealing_document.id


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
            'document_id': instance.document.pk,
            'pk': instance.pk,
        })

    def get_download_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-attachments-download', request=self.context['request'], kwargs={
            'document_id': instance.document.pk,
            'pk': instance.pk,
        })

    def get_view_url(self, instance):
        if not instance.pk:
            return None
        return reverse('document-attachments-view', request=self.context['request'], kwargs={
            'document_id': instance.document.pk,
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


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'display_name')
        read_only_fields = fields

    def get_display_name(self, user):
        if user.first_name:
            name = user.first_name
            if user.last_name:
                name += ' %s.' % user.last_name[0]
        else:
            name = user.username

        return name


class RevisionSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(source='date_created')
    user = UserSerializer()

    class Meta:
        model = reversion.models.Revision
        fields = ('id', 'date', 'comment', 'user')
        read_only_fields = fields


class DocumentListSerializer(serializers.ListSerializer):
    def __init__(self, *args, **kwargs):
        if 'child' not in kwargs:
            kwargs['child'] = DocumentSerializer()

        super(DocumentListSerializer, self).__init__(*args, **kwargs)
        # mark on the child that we're doing many, so it doesn't
        # try to decorate the children for us
        self.context['many'] = True

    def to_representation(self, data):
        iterable = data.all() if isinstance(data, Manager) else data

        # Do some bulk post-processing, this is much more efficient
        # than doing each document one at a time and going to the DB
        # hundreds of times.
        Document.decorate_amended_versions(iterable)
        Document.decorate_repeal(iterable)

        return super(DocumentListSerializer, self).to_representation(data)


class DocumentSerializer(serializers.HyperlinkedModelSerializer):
    content = serializers.CharField(required=False, write_only=True)
    """ A write-only field for setting the entire XML content of the document. """

    content_url = serializers.SerializerMethodField()
    """ A URL for the entire content of the document. The content isn't included in the
    document description because it could be huge. """

    toc_url = serializers.SerializerMethodField()
    """ A URL for the table of content of the document. The TOC isn't included in the
    document description because it could be huge and requires parsing the XML. """

    published_url = serializers.SerializerMethodField()
    """ Public URL of a published document. """

    attachments_url = serializers.SerializerMethodField()
    """ URL of document attachments. """

    annotations_url = serializers.SerializerMethodField()
    """ URL of document annotations. """

    links = serializers.SerializerMethodField()
    """ List of alternate links. """

    file = serializers.FileField(write_only=True, required=False)
    """ Allow uploading a file to convert and override the content of the document. """

    file_options = serializers.DictField(write_only=True, required=False)
    """ Options when importing a new document using the +file+ field. """

    draft = serializers.BooleanField(default=True)

    # if a title isn't given, it's taken from the associated work
    title = serializers.CharField(required=False, allow_blank=False, allow_null=False)

    # taken from the work
    publication_name = serializers.CharField(read_only=True)
    publication_number = serializers.CharField(read_only=True)
    publication_date = serializers.DateField(read_only=True)
    commencement_date = serializers.DateField(read_only=True)
    assent_date = serializers.DateField(read_only=True)

    tags = TagListSerializerField(required=False)
    amendments = AmendmentEventSerializer(many=True, read_only=True, source='amendment_events')

    amended_versions = serializers.SerializerMethodField()
    """ List of amended versions of this document """
    repeal = RepealSerializer(read_only=True)
    """ Repeal information, inherited from the work. """

    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)

    class Meta:
        list_serializer_class = DocumentListSerializer
        model = Document
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'content', 'content_url', 'file', 'file_options', 'title', 'draft',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri',

            'publication_date', 'publication_name', 'publication_number',
            'expression_date', 'commencement_date', 'assent_date',
            'language', 'stub', 'tags', 'amendments', 'amended_versions',
            'repeal',

            'published_url', 'toc_url', 'attachments_url', 'links', 'annotations_url',
        )
        read_only_fields = ('locality', 'nature', 'subtype', 'year', 'number', 'created_at', 'updated_at')

    def get_content_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-content', request=self.context['request'], kwargs={'pk': doc.pk})

    def get_toc_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-toc', request=self.context['request'], kwargs={'pk': doc.pk})

    def get_attachments_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-attachments-list', request=self.context['request'], kwargs={'document_id': doc.pk})

    def get_annotations_url(self, doc):
        if not doc.pk:
            return None
        return reverse('document-annotations-list', request=self.context['request'], kwargs={'document_id': doc.pk})

    def get_published_url(self, doc, with_date=False):
        if not doc.pk or doc.draft:
            return None
        else:
            uri = doc.work_uri
            if with_date and doc.expression_date:
                uri.expression_date = '@' + datestring(doc.expression_date)
            else:
                uri.expression_date = None

            uri = uri.expression_uri()[1:]

            uri = reverse('published-document-detail', request=self.context['request'],
                          kwargs={'frbr_uri': uri})
            return uri.replace('%40', '@')

    def get_amended_versions(self, doc):
        def describe(doc):
            info = {
                'id': d.id,
                'expression_date': datestring(d.expression_date),
            }
            if not d.draft:
                info['published_url'] = self.get_published_url(d, with_date=True)
            return info

        return [describe(d) for d in doc.amended_versions()]

    def get_links(self, doc):
        if not doc.draft:
            url = self.get_published_url(doc)
            return [
                {
                    "rel": "alternate",
                    "title": "HTML",
                    "href": url + ".html",
                    "mediaType": "text/html"
                },
                {
                    "rel": "alternate",
                    "title": "Standalone HTML",
                    "href": url + ".html?standalone=1",
                    "mediaType": "text/html"
                },
                {
                    "rel": "alternate",
                    "title": "Akoma Ntoso",
                    "href": url + ".xml",
                    "mediaType": "application/xml"
                },
                {
                    "rel": "alternate",
                    "title": "Table of Contents",
                    "href": url + "/toc.json",
                    "mediaType": "application/json"
                },
                {
                    "rel": "alternate",
                    "title": "PDF",
                    "href": url + ".pdf",
                    "mediaType": "application/pdf"
                },
                {
                    "rel": "alternate",
                    "title": "ePUB",
                    "href": url + ".epub",
                    "mediaType": "application/epub+zip"
                },
            ]

    def validate(self, data):
        """
        We allow callers to pass in a file upload in the ``file`` attribute,
        and overwrite the content XML with that value if we can.
        """
        upload = data.pop('file', None)
        if upload:
            frbr_uri = self.validate_frbr_uri(data.get('frbr_uri'))

            # we got a file
            try:
                # import options
                opts = data.get('file_options', {})
                posn = opts.get('section_number_position', 'guess')
                cropbox = opts.get('cropbox', None)
                if cropbox:
                    cropbox = cropbox.split(',')
                request = self.context['request']

                country = data.get('country') or request.user.editor.country_code
                importer = importers.for_locale(country, None, None)

                importer.section_number_position = posn
                importer.cropbox = cropbox
                document = importer.import_from_upload(upload, frbr_uri, request)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})
            data['content'] = document.content
            # add the document as an attachment
            data['source_file'] = upload

        return data

    def validate_content(self, value):
        try:
            Act(value)
        except LxmlError as e:
            raise ValidationError("Invalid XML: %s" % e.message)
        return value

    def validate_frbr_uri(self, value):
        try:
            if not value:
                raise ValueError()
            value = FrbrUri.parse(value.lower()).work_uri()
        except ValueError:
            raise ValidationError("Invalid FRBR URI: %s" % value)

        # does a work exist for this frbr_uri?
        # raises ValueError if it doesn't
        Work.objects.get_for_frbr_uri(value)

        return value

    def create(self, validated_data):
        document = Document()
        return self.update(document, validated_data)

    def update(self, document, validated_data):
        """ Update and save document. """
        source_file = validated_data.pop('source_file', None)
        tags = validated_data.pop('tags', None)

        self.update_document(document, validated_data)

        user = self.context['request'].user
        if user:
            document.updated_by_user = user
            if not document.created_by_user:
                document.created_by_user = user

        # save as a revision
        document.save_with_revision(user)

        # these require that the document is saved
        if tags is not None:
            document.tags.set(*tags)

        if source_file:
            # add the source file as an attachment
            AttachmentSerializer(context={'document': document}).create({'file': source_file})

        # reload it to ensure tags are refreshed
        document = Document.objects.get(pk=document.id)
        return document

    def update_document(self, document, validated_data=None):
        """ Update document without saving it. """
        if validated_data is None:
            validated_data = self.validated_data

        # Document content must always come first so it can be overridden
        # by the other properties.
        content = validated_data.pop('content', None)
        if content is not None:
            document.content = content

        # save rest of changes
        for attr, value in validated_data.items():
            setattr(document, attr, value)

        # Link to the appropriate work, based on the FRBR URI
        # Raises ValueError if the work doesn't exist
        document.work = Work.objects.get_for_frbr_uri(document.frbr_uri)

        document.copy_attributes()
        return document

    def to_representation(self, instance):
        if not self.context.get('many', False):
            Document.decorate_amended_versions([instance])
            Document.decorate_repeal([instance])
        return super(DocumentSerializer, self).to_representation(instance)


class RenderSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /render API
    """
    document = DocumentSerializer()


class ParseSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /parse API
    """
    file = serializers.FileField(write_only=True, required=False)
    content = serializers.CharField(write_only=True, required=False)
    fragment = serializers.CharField(write_only=True, required=False)
    id_prefix = serializers.CharField(write_only=True, required=False)
    frbr_uri = serializers.CharField(write_only=True, required=True)


class DocumentAPISerializer(serializers.Serializer):
    """
    Helper to handle input documents for general document APIs
    """
    document = DocumentSerializer(required=True)


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


class AnnotationSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    created_by_user = UserSerializer(read_only=True)
    anchor = AnnotationAnchorSerializer()
    in_reply_to = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects, allow_null=True, required=False)

    class Meta:
        model = Annotation
        fields = (
            'id',
            'url',
            'text',
            'anchor',
            'in_reply_to',
            'closed',
            'created_by_user',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_by_user', 'in_reply_to', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by_user'] = self.context['request'].user
        validated_data['document'] = self.context['document']
        validated_data['anchor_id'] = validated_data.pop('anchor').get('id')
        return super(AnnotationSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if 'in_reply_to' in validated_data:
            del validated_data['in_reply_to']

        validated_data['anchor_id'] = validated_data.pop('anchor').get('id')
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
            'document_id': instance.document.pk,
            'pk': instance.pk,
        })


class DocumentActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = DocumentActivity
        fields = (
            'user',
            'created_at',
            'updated_at',
            'nonce',
            'is_asleep',
        )
        read_only_fields = ('created_at', 'updated_at')
        extra_kwargs = {'nonce': {'required': True}}

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['document'] = self.context['document']
        return super(DocumentActivitySerializer, self).create(validated_data)


class WorkSerializer(serializers.ModelSerializer):
    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)
    repealed_by = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')
    parent_work = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')
    commencing_work = SerializedRelatedField(queryset=Work.objects, required=False, allow_null=True, serializer='WorkSerializer')

    amendments_url = serializers.SerializerMethodField()
    """ URL of document amendments. """

    class Meta:
        model = Work
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'title', 'publication_name', 'publication_number', 'publication_date',
            'commencement_date', 'assent_date',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',
            'parent_work', 'commencing_work', 'amendments_url',

            # repeal
            'repealed_date', 'repealed_by',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri',
        )
        read_only_fields = ('locality', 'nature', 'subtype', 'year', 'number', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by_user'] = self.context['request'].user
        return super(WorkSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by_user'] = self.context['request'].user
        return super(WorkSerializer, self).update(instance, validated_data)

    def validate_frbr_uri(self, value):
        try:
            value = FrbrUri.parse(value.lower()).work_uri()
        except ValueError:
            raise ValidationError("Invalid FRBR URI: %s" % value)
        return value

    def get_amendments_url(self, work):
        if not work.pk:
            return None
        return reverse('work-amendments-list', request=self.context['request'], kwargs={'work_id': work.pk})


class WorkAmendmentSerializer(serializers.ModelSerializer):
    updated_by_user = UserSerializer(read_only=True)
    created_by_user = UserSerializer(read_only=True)
    amending_work = SerializedRelatedField(queryset=Work.objects, required=True, allow_null=False, serializer=WorkSerializer)
    url = serializers.SerializerMethodField()

    class Meta:
        model = Amendment
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'amending_work', 'date',
            'updated_by_user', 'created_by_user',
            'created_at', 'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['created_by_user'] = self.context['request'].user
        validated_data['amended_work'] = self.context['work']
        return super(WorkAmendmentSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        validated_data['updated_by_user'] = self.context['request'].user
        return super(WorkAmendmentSerializer, self).update(instance, validated_data)

    def get_url(self, instance):
        if not instance.pk:
            return None
        return reverse('work-amendments-detail', request=self.context['request'], kwargs={
            'work_id': instance.amended_work.pk,
            'pk': instance.pk,
        })
