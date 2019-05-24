from itertools import groupby

from rest_framework import serializers
from rest_framework.reverse import reverse
from cobalt.act import datestring

from indigo_api.models import Document, Attachment, Country, Locality, PublicationDocument
from indigo_api.serializers import DocumentSerializer, PublicationDocumentSerializer, AttachmentSerializer


def published_doc_url(doc, request, frbr_uri=None):
    """ Absolute URL for a published document.
    eg. /api/v1/za/acts/2005/01/eng@2006-02-03
    """
    uri = (frbr_uri or doc.expression_uri.expression_uri())[1:]
    uri = reverse('published-document-detail', request=request, kwargs={'frbr_uri': uri})
    return uri.replace('%40', '@')


class PublishedPublicationDocumentSerializer(PublicationDocumentSerializer):
    def get_url(self, instance):
        if instance.trusted_url:
            return instance.trusted_url
        uri = published_doc_url(self.context['document'], self.context['request'])
        return uri + '/media/' + instance.filename


class ExpressionSerializer(serializers.Serializer):
    url = serializers.SerializerMethodField()
    language = serializers.CharField(source='language.code')
    expression_frbr_uri = serializers.SerializerMethodField()
    expression_date = serializers.DateField()
    title = serializers.CharField()

    class Meta:
        fields = ('url', 'language', 'expression_frbr_uri', 'title', 'expression_date')
        read_only_fields = fields

    def get_url(self, doc):
        return published_doc_url(doc, self.context['request'])

    def get_expression_frbr_uri(self, doc):
        return doc.expression_uri.expression_uri()


class MediaAttachmentSerializer(AttachmentSerializer):
    class Meta:
        model = Attachment
        fields = ('url', 'filename', 'mime_type', 'size')
        read_only_fields = fields

    def get_url(self, instance):
        uri = published_doc_url(instance.document, self.context['request'])
        return uri + '/media/' + instance.filename


class PublishedDocumentSerializer(DocumentSerializer):
    """ Serializer for published documents.

    Inherits most fields from the base document serializer.
    """
    url = serializers.SerializerMethodField()
    points_in_time = serializers.SerializerMethodField()
    publication_document = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'url', 'title',
            'created_at', 'updated_at',

            # frbr_uri components
            'country', 'locality', 'nature', 'subtype', 'year', 'number', 'frbr_uri', 'expression_frbr_uri',

            'publication_date', 'publication_name', 'publication_number', 'publication_document',
            'expression_date', 'commencement_date', 'assent_date',
            'language', 'repeal', 'amendments', 'points_in_time',

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

        return PublishedPublicationDocumentSerializer(
            context={'document': doc, 'request': self.context['request']}
        ).to_representation(pub_doc)

    def get_url(self, doc):
        return self.context.get('url', published_doc_url(doc, self.context['request']))

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


class LocalitySerializer(serializers.ModelSerializer):
    frbr_uri_code = serializers.SerializerMethodField()
    links = serializers.SerializerMethodField()

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
        return '%s-%s' % (instance.country.code, instance.code)

    def get_links(self, instance):
        return [
            {
                "rel": "works",
                "title": "Works",
                "href": reverse(
                    'published-document-detail',
                    request=self.context['request'],
                    kwargs={'frbr_uri': '%s-%s/' % (instance.country.code, instance.code)}),
            },
        ]


class CountrySerializer(serializers.ModelSerializer):
    localities = LocalitySerializer(many=True)
    links = serializers.SerializerMethodField()
    """ List of alternate links. """

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
                "href": reverse('published-document-detail', request=self.context['request'], kwargs={'frbr_uri': '%s/' % instance.code}),
            },
            {
                "rel": "search",
                "title": "Search",
                "href": reverse('public-search', request=self.context['request'], kwargs={'country': instance.code}),
            },
        ]
