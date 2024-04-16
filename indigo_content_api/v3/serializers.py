from indigo_content_api.v2.serializers import PublishedDocumentSerializer as PublishedDocumentSerializerV2


class PublishedDocumentSerializerV3(PublishedDocumentSerializerV2):
    # Excludes detailed commencement information.
    commencements = None

    class Meta:
        model = PublishedDocumentSerializerV2.Meta.model
        fields = tuple(x for x in PublishedDocumentSerializerV2.Meta.fields if x not in ['commencements'])
        read_only_fields = fields
