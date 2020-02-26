import re

from rest_framework import renderers

from indigo_api.renderers import AkomaNtosoRenderer, PDFRenderer, EPUBRenderer, HTMLRenderer, ZIPRenderer
from indigo_content_api.v1.views import PublishedDocumentDetailView, PublishedDocumentTOCView


def rewrite_frbr_uris(data):
    """ Recursively rewrite entries in data that are FRBR URIs, to ensure they start with /akn/
    """
    if isinstance(data, dict):
        for key, val in data.items():
            if key.endswith('frbr_uri') or key == 'amending_uri' or key == 'repealing_uri':
                if val and not val.startswith('/akn'):
                    data[key] = '/akn' + val

            if isinstance(val, dict):
                rewrite_frbr_uris(val)

            elif isinstance(val, list):
                for x in val:
                    rewrite_frbr_uris(x)


class PublishedDocumentDetailViewV2(PublishedDocumentDetailView):
    # Note that the V2 API doesn't support Atom
    renderer_classes = (renderers.JSONRenderer, PDFRenderer, EPUBRenderer, AkomaNtosoRenderer, HTMLRenderer,
                        ZIPRenderer)

    non_akn_href_re = re.compile(r'^/[a-z]{2}[/-].*')

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(PublishedDocumentDetailViewV2, self).finalize_response(request, response, *args, **kwargs)
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
            if v and not v.startswith('/akn'):
                elem.set('value', '/akn' + v)

        for ref in document.doc.root.xpath('//a:ref[@href]', namespaces={'a': document.doc.namespace}):
            v = ref.get('href') or ''
            if v and self.non_akn_href_re.match(v):
                ref.set('href', '/akn' + v)

        document.refresh_xml()
