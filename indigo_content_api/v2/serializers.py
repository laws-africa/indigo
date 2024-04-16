from itertools import groupby
from typing import List

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_serializer, extend_schema_field
from rest_framework import serializers

from cobalt import datestring

from indigo_api.models import Document, Attachment, Country, Locality, PublicationDocument, TaxonomyTopic, \
    Amendment
from indigo_api.serializers import \
    DocumentSerializer, AttachmentSerializer, CommencementSerializer, \
    PublicationDocumentSerializer as PublicationDocumentSerializerBase
from indigo_api.timeline import TimelineEventType
from indigo_content_api.reverse import reverse_content_api


class PublishedDocUrlMixin:
    def published_doc_url(self, doc, request, frbr_uri=None):
        """ Absolute URL for a published document.
        eg. /api/v2/akn/za/act/2005/01/eng@2006-02-03
        """
        uri = (frbr_uri or doc.expression_uri.expression_uri())[1:]
        uri = reverse_content_api('indigo_content_api:published-document-detail', request=request, kwargs={'frbr_uri': uri})
        return uri.replace('%40', '@')

    def place_url(self, request, code):
        if self.prefix:
            code = 'akn/' + code
        return reverse_content_api('indigo_content_api:published-document-detail', request=request, kwargs={'frbr_uri': code})


class ExpressionSerializer(serializers.Serializer, PublishedDocUrlMixin):
    """Details of an expression of a work."""
    url = serializers.SerializerMethodField(help_text="URL for full details of this work expression.")
    language = serializers.CharField(source='language.code', help_text="Three letter ISO-639-2 language code")
    expression_frbr_uri = serializers.CharField(help_text="FRBR URI of this expression.")
    expression_date = serializers.DateField(help_text="Date of this expression")
    title = serializers.CharField(help_text="Title of this expression, which may be different to the title of the work.")

    class Meta:
        fields = ('url', 'language', 'expression_frbr_uri', 'title', 'expression_date')
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, doc):
        return self.published_doc_url(doc, self.context['request'])


class MediaAttachmentSerializer(AttachmentSerializer, PublishedDocUrlMixin):
    class Meta:
        model = Attachment
        fields = ('url', 'filename', 'mime_type', 'size')
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, instance):
        uri = self.published_doc_url(instance.document, self.context['request'])
        return uri + '/media/' + instance.filename


class PublicationDocumentSerializer(PublicationDocumentSerializerBase):
    """Details of the original publication document for a work."""
    class Meta:
        model = PublicationDocument
        # Don't include the trusted_url field
        fields = ('url', 'filename', 'mime_type', 'size')

    @extend_schema_field(OpenApiTypes.URI)
    def get_url(self, instance):
        if instance.trusted_url:
            return instance.trusted_url

        # the publication document is linked to the work, not the expression
        uri = (instance.work.work_uri.work_uri())[1:]
        return reverse_content_api('indigo_content_api:published-document-publication',
                                   request=self.context['request'],
                                   kwargs={'frbr_uri': uri, 'filename': instance.filename})


class AmendmentSerializer(serializers.ModelSerializer):
    amending_title = serializers.CharField(source='amending_work.title', help_text="Title of the amending work.")
    amending_uri = serializers.CharField(source='amending_work.frbr_uri', help_text="FRBR URI of the amending work.")

    class Meta:
        model = Amendment
        fields = (
            'date', 'amending_title', 'amending_uri'
        )
        read_only_fields = fields


@extend_schema_serializer(component_name="Commencements", many=False)
class PublishedDocumentCommencementsSerializer(serializers.Serializer, PublishedDocUrlMixin):
    commencements = CommencementSerializer(many=True, source='work.commencements')

    class Meta:
        fields = ('commencements',)
        read_only_fields = fields


# matches indigo.analysis.toc.base.TOCElement
class TOCEntrySerializer(serializers.Serializer):
    """An entry in a document's Table of Contents (TOC)."""
    type = serializers.CharField(help_text="Type of entry, one of the AKN hierarchical elements.")
    component = serializers.CharField(
        help_text="Component name (after the ! in the FRBR URI) of the component that this entry is a part of.")
    title = serializers.CharField(
        help_text="Friendly title of this entry, taking heading, type and number into account.")
    basic_unit = serializers.BooleanField(help_text="Is this a basic unit in the country's local tradition?")
    num = serializers.CharField(help_text="Text of the AKN num element.")
    id = serializers.CharField(help_text="eId of this entry, if it has one.")
    heading = serializers.CharField(help_text="Text of the AKN heading element, if it has one.")
    children = serializers.SerializerMethodField()
    url = serializers.URLField(help_text="URL for content for this element.")

    class Meta:
        fields = ('type', 'component', 'title', 'basic_unit', 'num', 'id', 'heading', 'children')
        read_only_fields = fields

    def get_fields(self):
        # adjust field definition for use with drf-spectacular
        fields = super().get_fields()
        fields['children'] = TOCEntrySerializer(many=True)
        return fields


@extend_schema_serializer(many=False)
class TOCSerializer(serializers.Serializer):
    """Table of Contents for a document."""
    toc = TOCEntrySerializer(many=True)


# matches indigo_api.timeline.TimelineEvent
class TimelineEventSerializer(serializers.Serializer):
    type = serializers.ChoiceField(TimelineEventType.choices, help_text="Type of the event.")
    description = serializers.CharField(help_text="Human-friendly description of the event.")
    by_frbr_uri = serializers.CharField(help_text="FRBR URI of the related work (if any) that caused this event.")
    by_title = serializers.CharField(help_text="Title of the related work (if any) that caused this event.")
    note = serializers.CharField(help_text="Additional human-friendly details associated with this event.")

    class Meta:
        fields = ('type', 'description', 'by_frbr_uri', 'by_title', 'note')
        read_only_fields = fields


# matches indigo_api.timeline.TimelineEntry
class TimelineEntrySerializer(serializers.Serializer):
    """An entry in a work's timeline."""
    date = serializers.DateField(help_text="Date of the events.")
    events = TimelineEventSerializer(many=True, help_text="The events at this date.")


@extend_schema_serializer(many=False)
class TimelineSerializer(serializers.Serializer):
    timeline = serializers.SerializerMethodField()

    class Meta:
        fields = ('timeline',)
        read_only_fields = fields

    def to_representation(self, doc):
        return {"timeline": doc.work.get_serialized_timeline()}

    def get_fields(self):
        # adjust field definition for use with drf-spectacular
        fields = super().get_fields()
        fields['timeline'] = TimelineEntrySerializer(many=True)
        return fields


class LinkSerializer(serializers.Serializer):
    """A link related to this object."""
    rel = serializers.CharField(help_text="The relationship of the link to the object.")
    title = serializers.CharField(help_text="Title of the link.")
    href = serializers.URLField()
    media_type = serializers.CharField(required=False, help_text="Mime type for the link.")

    class Meta:
        fields = ('rel', 'title', 'href')
        read_only_fields = fields


class RelatedWorkSerializer(serializers.Serializer):
    """Details of a related work."""
    frbr_uri = serializers.CharField(help_text="FRBR URI of the work")
    title = serializers.CharField(help_text="Title of the work")

    class Meta:
        fields = ('frbr_uri', 'title')
        read_only_fields = fields


class PointInTimeSerializer(serializers.Serializer):
    """Details of a point in time for a work."""
    date = serializers.DateField(help_text="Date of this point in time.")
    expressions = ExpressionSerializer(many=True, help_text="Expressions available at this point in time.")

    class Meta:
        fields = ('date', 'expressions')
        read_only_fields = fields


@extend_schema_serializer(component_name="WorkExpression")
class PublishedDocumentSerializer(DocumentSerializer, PublishedDocUrlMixin):
    """ Details of a published work expression (document). """
    country = serializers.CharField(help_text="ISO 3166-1 alpha-2 country code that this work belongs to.")
    locality = serializers.CharField(help_text="The code of the locality within the country.", required=False)
    nature = serializers.CharField(help_text="Doctype component of the work FRBR URI.")
    subtype = serializers.CharField(help_text="Subtype component of the work FRBR URI.", required=False)
    date = serializers.CharField(
        help_text="Date component of the work FRBR URI, in ISO8601 format. YYYY, YYYY-MM or YYYY-MM-DD.")
    year = serializers.CharField(help_text="Year portion of the FRBR date component the work FRBR URI.")
    actor = serializers.CharField(help_text="Actor component of the work FRBR URI.", required=False)
    number = serializers.CharField(help_text="Number component of the work FRBR URI.")

    url = serializers.SerializerMethodField(help_text="Detail URL for this work expression.")
    points_in_time = serializers.SerializerMethodField(help_text="Available historical versions of this work.")
    publication_document = serializers.SerializerMethodField(
        help_text="Details of the original publication document file for this work.")
    taxonomy_topics = serializers.SerializerMethodField(
        help_text="Slugs of the taxonomy topics applicable to this work.")
    as_at_date = serializers.DateField(source='work.as_at_date',
                                       help_text="The date at which this work is known to be up-to-date.")
    commenced = serializers.BooleanField(source='work.commenced', help_text="Whether this work has commenced.")
    commencements = CommencementSerializer(many=True, source='work.commencements',
                                           help_text="Details of the commencements which apply to this work.")
    work_amendments = AmendmentSerializer(many=True, source='work.amendments',
                                          help_text="Details of all amendments to this work.")
    parent_work = serializers.SerializerMethodField(help_text="Details of the parent work, for subsidiary works.")
    custom_properties = serializers.JSONField(source='work.labeled_properties',
                                              help_text="Custom key-value pairs for this work.")
    stub = serializers.BooleanField(source='work.stub', help_text="A stub work has no content, only metadata.")
    principal = serializers.BooleanField(
        source='work.principal',
        help_text="A principal work is a main work and not just a repealing, commencing or amending work.")
    aliases = serializers.SerializerMethodField(help_text="Well-known alternative names for this work.")

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
            'numbered_title', 'taxonomy_topics', 'as_at_date', 'stub', 'principal', 'type_name',
            'aliases',

            'links',
        )
        read_only_fields = fields

    @extend_schema_field(PointInTimeSerializer(many=True))
    def get_points_in_time(self, doc):
        result = []

        expressions = doc.work.expressions().published()
        for date, group in groupby(expressions, lambda e: e.expression_date):
            result.append({
                'date': datestring(date),
                'expressions': ExpressionSerializer(many=True, context=self.context).to_representation(group),
            })

        return result

    @extend_schema_field(PublicationDocumentSerializer)
    def get_publication_document(self, doc):
        try:
            pub_doc = doc.work.publication_document
        except PublicationDocument.DoesNotExist:
            return None

        return PublicationDocumentSerializer(
            context={'document': doc, 'request': self.context['request']}
        ).to_representation(pub_doc)

    @extend_schema_field(serializers.URLField)
    def get_url(self, doc):
        return self.context.get('url', self.published_doc_url(doc, self.context['request']))

    def get_taxonomy_topics(self, doc) -> List[str]:
        from indigo_api.serializers import WorkSerializer
        return WorkSerializer().get_taxonomy_topics(doc.work)

    @extend_schema_field(RelatedWorkSerializer)
    def get_parent_work(self, doc):
        if doc.work.parent_work:
            return {
                'frbr_uri': doc.work.parent_work.frbr_uri,
                'title': doc.work.parent_work.title,
            }

    def get_aliases(self, doc) -> List[str]:
        return [x.alias for x in doc.work.aliases.all()]

    @extend_schema_field(LinkSerializer(many=True))
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
    frbr_uri_code = serializers.SerializerMethodField(help_text="Complete FRBR URI code for this locality.")
    links = serializers.SerializerMethodField(help_text="A list of alternate links for this locality.")
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

    @extend_schema_field(OpenApiTypes.STR)
    def get_frbr_uri_code(self, instance):
        return '%s-%s' % (instance.country.code, instance.code)

    @extend_schema_field(LinkSerializer(many=True))
    def get_links(self, instance):
        """A list of alternate links for this locality."""
        return [
            {
                "rel": "works",
                "title": "Works",
                "href": self.place_url(self.context['request'], f"{instance.country.code}-{instance.code}/"),
            },
        ]


class PlaceSerializer(serializers.ModelSerializer, PublishedDocUrlMixin):
    frbr_uri_code = serializers.CharField(help_text="FRBR URI code for this place.", source='place_code')
    localities = LocalitySerializer(many=True, help_text="Localities within this place.", required=False)
    links = serializers.SerializerMethodField(help_text="A list of alternate links for this place.")
    prefix = True

    class Meta:
        model = Country
        fields = (
            'code',
            'name',
            'frbr_uri_code',
            'localities',
            'links',
        )
        read_only_fields = fields

    @extend_schema_field(LinkSerializer(many=True))
    def get_links(self, instance):
        return [
            {
                "rel": "works",
                "title": "Works",
                "href": self.place_url(self.context['request'], f"{instance.place_code}/"),
            },
        ]


class TaxonomyTopicSerializer(serializers.ModelSerializer):
    """ Details of an entry in the taxonomy topic tree. """
    # fake field for drf-spectacular
    children = serializers.SerializerMethodField(help_text="Children of this taxonomy topic.")

    class Meta:
        model = TaxonomyTopic
        fields = ('name', 'slug', 'id', 'children')

    _fields = ['name', 'slug', 'id']

    def to_representation(self, instance):
        data = TaxonomyTopic.dump_bulk(instance)[0]
        def fix(node):
            # move data out of "data" object
            data = node['data']
            data['id'] = node['id']
            for key in list(data.keys()):
                if key not in self._fields:
                    del data[key]
            data['children'] = [fix(n) for n in node.get('children', [])]
            return data
        return fix(data)

    def get_fields(self):
        # add children field to definition for use with drf-spectacular
        fields = super().get_fields()
        fields['children'] = TaxonomyTopicSerializer(many=True)
        return fields
