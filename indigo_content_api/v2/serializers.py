from itertools import groupby

from rest_framework import serializers

from cobalt import datestring

from indigo_api.models import Document, Attachment, Country, Locality, PublicationDocument, TaxonomyVocabulary, Amendment
from indigo_api.serializers import \
    DocumentSerializer, AttachmentSerializer, VocabularyTopicSerializer, CommencementSerializer, \
    PublicationDocumentSerializer as PublicationDocumentSerializerBase
from indigo_content_api.reverse import reverse_content_api


class PublishedDocUrlMixin:
    def published_doc_url(self, doc, request, frbr_uri=None):
        """ Absolute URL for a published document.
        eg. /api/v2/akn/za/act/2005/01/eng@2006-02-03
        """
        uri = (frbr_uri or doc.expression_uri.expression_uri())[1:]
        uri = reverse_content_api('published-document-detail', request=request, kwargs={'frbr_uri': uri})
        return uri.replace('%40', '@')

    def place_url(self, request, code):
        if self.prefix:
            code = 'akn/' + code
        return reverse_content_api('published-document-detail', request=request, kwargs={'frbr_uri': code})


class ExpressionSerializer(serializers.Serializer, PublishedDocUrlMixin):
    url = serializers.SerializerMethodField()
    language = serializers.CharField(source='language.code')
    expression_frbr_uri = serializers.CharField()
    expression_date = serializers.DateField()
    title = serializers.CharField()

    class Meta:
        fields = ('url', 'language', 'expression_frbr_uri', 'title', 'expression_date')
        read_only_fields = fields

    def get_url(self, doc):
        return self.published_doc_url(doc, self.context['request'])


class MediaAttachmentSerializer(AttachmentSerializer, PublishedDocUrlMixin):
    class Meta:
        model = Attachment
        fields = ('url', 'filename', 'mime_type', 'size')
        read_only_fields = fields

    def get_url(self, instance):
        uri = self.published_doc_url(instance.document, self.context['request'])
        return uri + '/media/' + instance.filename


class PublicationDocumentSerializer(PublicationDocumentSerializerBase):
    class Meta:
        model = PublicationDocument
        # Don't include the trusted_url field
        fields = ('url', 'filename', 'mime_type', 'size')

    def get_url(self, instance):
        if instance.trusted_url:
            return instance.trusted_url

        # the publication document is linked to the work, not the expression
        uri = (instance.work.work_uri.work_uri())[1:]
        return reverse_content_api('published-document-publication', request=self.context['request'],
                                   kwargs={'frbr_uri': uri, 'filename': instance.filename})


class AmendmentSerializer(serializers.ModelSerializer):
    amending_title = serializers.CharField(source='amending_work.title')
    amending_uri = serializers.CharField(source='amending_work.frbr_uri')

    class Meta:
        model = Amendment
        fields = (
            'date', 'amending_title', 'amending_uri'
        )
        read_only_fields = fields


class PublishedDocumentSerializer(DocumentSerializer, PublishedDocUrlMixin):
    """ Serializer for published documents.

    Inherits most fields from the base document serializer.
    """
    url = serializers.SerializerMethodField()
    points_in_time = serializers.SerializerMethodField()
    publication_document = serializers.SerializerMethodField()
    taxonomies = serializers.SerializerMethodField()
    as_at_date = serializers.DateField(source='work.as_at_date')
    commenced = serializers.BooleanField(source='work.commenced')
    commencements = CommencementSerializer(many=True, source='work.commencements')
    work_amendments = AmendmentSerializer(many=True, source='work.amendments')
    parent_work = serializers.SerializerMethodField()
    custom_properties = serializers.JSONField(source='work.labeled_properties')
    stub = serializers.BooleanField(source='work.stub')
    principal = serializers.BooleanField(source='work.principal')

    class Meta:
        model = Document
        fields = (
            'url', 'title',
            'created_at', 'updated_at',

            # frbr_uri components
            # year is for backwards compatibility
            'country', 'locality', 'nature', 'subtype', 'date', 'year', 'actor', 'number', 'frbr_uri', 'expression_frbr_uri',

            'publication_date', 'publication_name', 'publication_number', 'publication_document',
            'expression_date', 'commenced', 'commencement_date', 'commencements', 'assent_date',
            'language', 'repeal', 'amendments', 'work_amendments', 'points_in_time', 'parent_work', 'custom_properties',
            'numbered_title', 'taxonomies', 'as_at_date', 'stub', 'principal', 'type_name',

            'links',
        )
        read_only_fields = fields

    def get_points_in_time(self, doc):
        result = []

        expressions = doc.work.expressions().published()
        for date, group in groupby(expressions, lambda e: e.expression_date):
            result.append({
                'date': datestring(date),
                'expressions': ExpressionSerializer(many=True, context=self.context).to_representation(group),
            })

        return result

    def get_publication_document(self, doc):
        try:
            pub_doc = doc.work.publication_document
        except PublicationDocument.DoesNotExist:
            return None

        return PublicationDocumentSerializer(
            context={'document': doc, 'request': self.context['request']}
        ).to_representation(pub_doc)

    def get_url(self, doc):
        return self.context.get('url', self.published_doc_url(doc, self.context['request']))

    def get_taxonomies(self, doc):
        from indigo_api.serializers import WorkSerializer
        return WorkSerializer().get_taxonomies(doc.work)

    def get_parent_work(self, doc):
        if doc.work.parent_work:
            return {
                'frbr_uri': doc.work.parent_work.frbr_uri,
                'title': doc.work.parent_work.title,
            }

    def get_links(self, doc):
        if not doc.draft:
            url = self.get_url(doc)
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
                {
                    "rel": "toc",
                    "title": "Table of Contents",
                    "href": url + '/toc.json',
                    "mediaType": "application/json"
                },
                {
                    "rel": "media",
                    "title": "Media",
                    "href": url + '/media.json',
                    "mediaType": "application/json"
                },
            ]


class LocalitySerializer(serializers.ModelSerializer, PublishedDocUrlMixin):
    frbr_uri_code = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()
    prefix = True

    class Meta:
        model = Locality
        fields = (
            'code',
            'name',
            'frbr_uri_code',
            'links',
        )
        read_only_fields = fields

    def get_frbr_uri_code(self, instance):
        return f'{instance.country.code}-{instance.code}'

    def get_links(self, instance):
        return [
            {
                "rel": "works",
                "title": "Works",
                "href": self.place_url(self.context['request'], f"{instance.country.code}-{instance.code}/"),
            },
        ]


class CountrySerializer(serializers.ModelSerializer, PublishedDocUrlMixin):
    localities = LocalitySerializer(many=True)
    links = serializers.SerializerMethodField()
    """ List of alternate links. """
    prefix = True

    class Meta:
        model = Country
        fields = (
            'code',
            'name',
            'localities',
            'links',
        )
        read_only_fields = fields

    def get_links(self, instance):
        return [
            {
                "rel": "works",
                "title": "Works",
                "href": self.place_url(self.context['request'], f"{instance.code}/"),
            },
        ]


class TaxonomySerializer(serializers.ModelSerializer):
    topics = VocabularyTopicSerializer(many=True, read_only=True)
    vocabulary = serializers.CharField(source='slug')

    class Meta:
        model = TaxonomyVocabulary
        fields = ['vocabulary', 'title', 'topics']


