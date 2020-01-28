import logging
import os.path
from itertools import groupby
import json

from actstream.signals import action
from collections import OrderedDict

from lxml.etree import LxmlError

from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from taggit_serializer.serializers import TagListSerializerField
from cobalt import Act, FrbrUri
import reversion

from indigo_api.models import Document, Attachment, Annotation, DocumentActivity, Work, Amendment, Language, \
    PublicationDocument, Task, VocabularyTopic
from indigo_api.signals import document_published
from allauth.account.utils import user_display

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
    """ Serializer matching :class:`cobalt.act.AmendmentEvent`
    """

    date = serializers.DateField()
    """ Date that the amendment took place """
    amending_title = serializers.CharField()
    """ Title of amending document """
    amending_uri = serializers.CharField()
    """ FRBR URI of amending document """


class RepealSerializer(serializers.Serializer):
    """ Serializer matching :class:`cobalt.act.RepealEvent`, for use describing
    the repeal on a published document.
    """

    date = serializers.DateField()
    """ Date that the repeal took place """
    repealing_title = serializers.CharField()
    """ Title of repealing document """
    repealing_uri = serializers.CharField()
    """ FRBR URI of repealing document """


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
        # the API might live on a different host
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

    links = serializers.SerializerMethodField()
    """ List of alternate links. """

    draft = serializers.BooleanField(default=True)
    language = serializers.CharField(source='language.code', required=True)
    expression_frbr_uri = serializers.CharField(read_only=True)

    # if a title isn't given, it's taken from the associated work
    title = serializers.CharField(required=False, allow_blank=False, allow_null=False)

    # taken from the work
    publication_name = serializers.CharField(read_only=True)
    publication_number = serializers.CharField(read_only=True)
    publication_date = serializers.DateField(read_only=True)
    commencement_date = serializers.DateField(read_only=True)
    assent_date = serializers.DateField(read_only=True)
    numbered_title = serializers.DateField(read_only=True, source='work.numbered_title')

    tags = TagListSerializerField(required=False)
    amendments = AmendmentEventSerializer(many=True, read_only=True, source='amendment_events')

    """ List of amended versions of this document """
    repeal = RepealSerializer(read_only=True)
    """ Repeal information, inherited from the work. """

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
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri', 'expression_frbr_uri',

            'publication_date', 'publication_name', 'publication_number',
            'expression_date', 'commencement_date', 'assent_date',
            'language', 'tags', 'amendments', 'repeal', 'numbered_title',

            'links',
        )
        read_only_fields = ('country', 'locality', 'nature', 'subtype', 'year', 'number', 'created_at', 'updated_at')

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

    def validate_content(self, value):
        try:
            Act(value)
        except LxmlError as e:
            raise ValidationError("Invalid XML: %s" % str(e))
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

    def validate_language(self, value):
        try:
            return Language.for_code(value)
        except Language.DoesNotExist:
            raise ValidationError("Invalid language: %s" % value)

    def create(self, validated_data):
        document = Document()
        return self.update(document, validated_data)

    def update(self, document, validated_data):
        """ Update and save document. """
        tags = validated_data.pop('tags', None)
        draft = document.draft

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

        # reload it to ensure tags are refreshed and we have an id for new documents
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


class RenderSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /render API
    """
    document = DocumentSerializer()


class ParseSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /parse API
    """
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


class TaskSerializer(serializers.ModelSerializer):
    created_by_user = UserSerializer(read_only=True)
    updated_by_user = UserSerializer(read_only=True)
    country = serializers.CharField(source='country.code')
    locality = serializers.CharField(source='locality.code')
    work = serializers.CharField(source='work.frbr_uri')
    annotation = serializers.PrimaryKeyRelatedField(queryset=Annotation.objects, required=False, allow_null=True)
    assigned_to = UserSerializer(read_only=True)

    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'country',
            'locality',
            'work',
            'document',
            'state',
            'labels',
            'assigned_to',
            'annotation',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',
        )
        read_only_fields = fields


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
    country = serializers.CharField(source='country.code', required=True)
    locality = serializers.CharField(source='locality_code', required=False, allow_null=True)
    publication_document = PublicationDocumentSerializer(read_only=True)
    taxonomies = serializers.SerializerMethodField()
    amendments_url = serializers.SerializerMethodField()
    """ URL of document amendments. """

    class Meta:
        model = Work
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',
            'title', 'publication_name', 'publication_number', 'publication_date', 'publication_document',
            'commenced', 'commencement_date', 'assent_date', 'stub',
            'created_at', 'updated_at', 'updated_by_user', 'created_by_user',
            'parent_work', 'commencing_work', 'amendments_url',

            # repeal
            'repealed_date', 'repealed_by',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri',

            # taxonomies
            'taxonomies',
        )
        read_only_fields = fields

    def get_amendments_url(self, work):
        if not work.pk:
            return None
        return reverse('work-amendments-list', request=self.context['request'], kwargs={'work_id': work.pk})

    def get_taxonomies(self, instance):
        taxonomies = []
        topics = sorted(instance.taxonomies.all(), key=lambda t: t.vocabulary.title)

        for vocab, group in groupby(topics, key=lambda t: t.vocabulary):
            taxonomies.append({
                "vocabulary": vocab.slug,
                "title": vocab.title,
                "topics": VocabularyTopicSerializer(many=True).to_representation(list(group)),
            })

        return taxonomies


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


class VocabularyTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = VocabularyTopic
        fields = ['level_1', 'level_2']


class DocumentDiffSerializer(serializers.Serializer):
    """ Helper to handle input elements for the /document/xxx/diff API
    """
    document = DocumentSerializer(required=True)
    element_id = serializers.CharField(required=False, allow_null=True)
