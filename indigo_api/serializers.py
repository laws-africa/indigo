import logging

from lxml.etree import LxmlError

from rest_framework import serializers, renderers
from rest_framework.reverse import reverse
from rest_framework.exceptions import ValidationError
from taggit_serializer.serializers import TagListSerializerField, TaggitSerializer
from cobalt import Act, FrbrUri

from .models import Document
from .importer import Importer

log = logging.getLogger(__name__)


class TagSerializer(TaggitSerializer):
    def _save_tags(self, tag_object, tags):
        for key in tags.keys():
            tag_values = tags.get(key)
            getattr(tag_object, key).set(*[tag for tag in tag_values])
        return tag_object


class DocumentSerializer(TagSerializer, serializers.HyperlinkedModelSerializer):
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

    file = serializers.FileField(write_only=True, required=False)
    """ Allow uploading a file to convert and override the content of the document. """

    publication_name = serializers.CharField(required=False, allow_blank=True)
    publication_number = serializers.CharField(required=False, allow_blank=True)
    publication_date = serializers.DateField(required=False)

    tags = TagListSerializerField(child=serializers.CharField(), required=False)

    class Meta:
        model = Document
        fields = (
            # readonly, url is part of the rest framework
            'id', 'url',

            'content', 'content_url', 'file',

            'title', 'draft', 'created_at', 'updated_at',
            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri',

            'publication_date', 'publication_name', 'publication_number',
            'commencement_date', 'assent_date',
            'language', 'stub', 'tags',

            'published_url', 'toc_url',
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

    def get_published_url(self, doc):
        if not doc.pk or doc.draft:
            return None
        else:
            uri = doc.doc.frbr_uri
            uri.expression_date = None
            uri = uri.expression_uri()[1:]

            return reverse('published-document-detail', request=self.context['request'],
                           kwargs={'frbr_uri': uri})

    def validate(self, data):
        """
        We allow callers to pass in a file upload in the ``file`` attribute,
        and overwrite the content XML with that value if we can.
        """
        upload = data.pop('file', None)
        if upload:
            # we got a file
            try:
                document = Importer().import_from_upload(upload)
            except ValueError as e:
                log.error("Error during import: %s" % e.message, exc_info=e)
                raise ValidationError({'file': e.message or "error during import"})
            data['content'] = document.content

        return data

    def validate_content(self, value):
        try:
            Act(value)
        except LxmlError as e:
            raise ValidationError("Invalid XML: %s" % e.message)
        return value

    def validate_frbr_uri(self, value):
        try:
            return FrbrUri.parse(value.lower()).work_uri()
        except ValueError:
            raise ValidationError("Invalid FRBR URI")

    def update_document(self, instance):
        """ Update document without saving it. """
        for attr, value in self.validated_data.items():
            setattr(instance, attr, value)
        instance.copy_attributes()
        return instance


class ConvertSerializer(serializers.Serializer):
    """
    Helper to handle input elements for the /convert API
    """

    file = serializers.FileField(write_only=True, required=False)
    content = serializers.CharField(write_only=True, required=False)
    inputformat = serializers.ChoiceField(write_only=True, required=False, choices=['application/json', 'text/plain'])
    outputformat = serializers.ChoiceField(write_only=True, required=True, choices=['application/xml', 'application/json', 'text/html'])
    fragment = serializers.CharField(write_only=True, required=False)
    id_prefix = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        if data.get('content') and not data.get('inputformat'):
            raise ValidationError({'inputformat': "The inputformat field is required when the content field is used"})

        return data


class AkomaNtosoRenderer(renderers.XMLRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        return data
