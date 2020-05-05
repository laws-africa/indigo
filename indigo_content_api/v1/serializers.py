from itertools import groupby

from cobalt import datestring

from indigo_api.models import PublicationDocument

from indigo_content_api.v2.serializers import PublishedDocUrlMixin, PublishedDocumentSerializer, \
    MediaAttachmentSerializer, ExpressionSerializer, PublicationDocumentSerializer, CountrySerializer, LocalitySerializer


class PublishedDocUrlMixinV1(PublishedDocUrlMixin):
    def published_doc_url(self, doc, request, frbr_uri=None):
        """ Absolute URL for a published document.
        eg. /api/v1/za/act/2005/01/eng@2006-02-03
        """
        uri = frbr_uri or doc.expression_uri.expression_uri()
        if uri.startswith('/akn'):
            uri = uri[4:]
        return super().published_doc_url(doc, request, frbr_uri=uri)


class ExpressionSerializerV1(ExpressionSerializer, PublishedDocUrlMixinV1):
    pass


class MediaAttachmentSerializerV1(MediaAttachmentSerializer, PublishedDocUrlMixinV1):
    pass


class PublicationDocumentSerializerV1(PublicationDocumentSerializer):
    def get_url(self, instance):
        if instance.work.frbr_uri.startswith('/akn'):
            instance.work.frbr_uri = instance.work.frbr_uri[4:]
        return super().get_url(instance)


class PublishedDocumentSerializerV1(PublishedDocumentSerializer, PublishedDocUrlMixinV1):
    def get_points_in_time(self, doc):
        # TODO: this should surely be simpler
        result = []

        expressions = doc.work.expressions().published()
        for date, group in groupby(expressions, lambda e: e.expression_date):
            result.append({
                'date': datestring(date),
                'expressions': ExpressionSerializerV1(many=True, context=self.context).to_representation(group),
            })

        return result

    def get_publication_document(self, doc):
        # TODO: this should surely be simpler
        try:
            pub_doc = doc.work.publication_document
        except PublicationDocument.DoesNotExist:
            return None

        return PublicationDocumentSerializerV1(
            context={'document': doc, 'request': self.context['request']}
        ).to_representation(pub_doc)


class LocalitySerializerV1(LocalitySerializer):
    prefix = False


class CountrySerializerV1(CountrySerializer):
    localities = LocalitySerializerV1(many=True)
    prefix = False
