import re

from indigo_content_api.v1.serializers import PublishedDocumentSerializerV1, MediaAttachmentSerializerV1, PublishedDocUrlMixinV1
from indigo_content_api.v2.views import PublishedDocumentDetailView, PublishedDocumentMediaView, PublishedDocumentTOCView


def rewrite_frbr_uris(data):
    """ Recursively rewrite entries in data that are FRBR URIs, to ensure they don't start with /akn/
    """
    if isinstance(data, dict):
        for key, val in data.items():
            if key.endswith('frbr_uri') or key == 'amending_uri' or key == 'repealing_uri':
                if val and val.startswith('/akn'):
                    data[key] = val[4:]

            if isinstance(val, dict):
                rewrite_frbr_uris(val)

            elif isinstance(val, list):
                for x in val:
                    rewrite_frbr_uris(x)


class PublishedDocumentDetailViewV1(PublishedDocumentDetailView):
    serializer_class = PublishedDocumentSerializerV1

    akn_href_re = re.compile(r'^/akn/[a-z]{2}[/-].*')

    def initial(self, request, **kwargs):
        # TODO: move this up to be reused
        # insert /akn prefix
        uri = self.kwargs['frbr_uri']
        if not uri.startswith('akn/'):
            self.kwargs['frbr_uri'] = 'akn/' + uri
        super().initial(request, **kwargs)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        renderer = getattr(response, 'accepted_renderer', None)

        if renderer:
            if renderer.media_type == 'application/json' and isinstance(response.data, dict):
                rewrite_frbr_uris(response.data)
            else:
                # for known renderers, rewrite akn data
                self.rewrite_akn(response.data)

        return response

    def rewrite_akn(self, document):
        if isinstance(document, list):
            for x in document:
                self.rewrite_akn(x)
            return

        if not hasattr(document, 'doc'):
            return

        for elem in document.doc.root.xpath('//a:FRBRuri | //a:FRBRthis', namespaces={'a': document.doc.namespace}):
            v = elem.get('value') or ''
            if v and v.startswith('/akn'):
                elem.set('value', v[4:])

        for ref in document.doc.root.xpath('//a:*[self::a:ref or self::a:passiveRef][@href]', namespaces={'a': document.doc.namespace}):
            v = ref.get('href') or ''
            if v and self.akn_href_re.match(v):
                ref.set('href', v[4:])

        document.refresh_xml()


class PublishedDocumentTOCViewV1(PublishedDocumentTOCView, PublishedDocUrlMixinV1):

    def initial(self, request, **kwargs):
        # TODO: move this up to be reused
        # insert /akn prefix
        uri = self.kwargs['frbr_uri']
        if not uri.startswith('akn/'):
            self.kwargs['frbr_uri'] = 'akn/' + uri
        super().initial(request, **kwargs)


class PublishedDocumentMediaViewV1(PublishedDocumentMediaView):
    serializer_class = MediaAttachmentSerializerV1

    def initial(self, request, **kwargs):
        # TODO: move this up to be reused
        # insert /akn prefix
        uri = self.kwargs['frbr_uri']
        if not uri.startswith('akn/'):
            self.kwargs['frbr_uri'] = 'akn/' + uri
        super().initial(request, **kwargs)
