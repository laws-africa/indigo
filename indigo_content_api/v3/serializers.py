from indigo_content_api.v2.serializers import PublishedDocumentSerializer as PublishedDocumentSerializerV2


class PublishedDocumentSerializerV3(PublishedDocumentSerializerV2):
    """ Serializer for published documents.
    Inherits most fields from the v2 published document serializer.
    - Excludes detailed commencement information.
    - Excludes taxonomies.
    """
    commencements = None
    taxonomies = None

    class Meta:
        model = PublishedDocumentSerializerV2.Meta.model
        fields = tuple(x for x in PublishedDocumentSerializerV2.Meta.fields if x not in ['commencements', 'taxonomies'])
        read_only_fields = fields
