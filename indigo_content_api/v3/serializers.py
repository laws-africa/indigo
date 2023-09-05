from indigo_content_api.v2.serializers import PublishedDocumentSerializer as PublishedDocumentSerializerV2


class PublishedDocumentSerializerV3(PublishedDocumentSerializerV2):
    """ Serializer for published documents.
    Inherits most fields from the v2 published document serializer.
    - Excludes detailed commencement information.
    - Excludes taxonomies.
    """
    # TODO: is this right, or just change Meta.fields?
    commencements = None
    taxonomies = None

    class Meta:
        # TODO: fine to have no model here (does it inherit from the base)?
        # TODO: inherit super fields, exclude 'commencements' and 'taxonomies'?
        fields = (
            'url', 'title',
            'created_at', 'updated_at',

            # frbr_uri components
            # year is for backwards compatibility
            'country', 'locality', 'nature', 'subtype', 'date', 'year', 'actor', 'number', 'frbr_uri', 'expression_frbr_uri',

            'publication_date', 'publication_name', 'publication_number', 'publication_document',
            'expression_date', 'commenced', 'commencement_date', 'assent_date',
            'language', 'repeal', 'amendments', 'work_amendments', 'points_in_time', 'parent_work', 'custom_properties',
            'numbered_title', 'taxonomy_topics', 'as_at_date', 'stub', 'principal', 'type_name',

            'links',
        )
        read_only_fields = fields
