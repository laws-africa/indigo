from __future__ import unicode_literals

import re

from rest_framework import renderers

from indigo_api.renderers import AkomaNtosoRenderer, PDFResponseRenderer, EPUBResponseRenderer, HTMLResponseRenderer, ZIPResponseRenderer
from indigo_content_api.v1.views import PublishedDocumentDetailView


class PublishedDocumentDetailViewV2(PublishedDocumentDetailView):
    # Note that the V2 API doesn't support Atom
    renderer_classes = (renderers.JSONRenderer, PDFResponseRenderer, EPUBResponseRenderer, AkomaNtosoRenderer, HTMLResponseRenderer,
                        ZIPResponseRenderer)

    non_akn_href_re = re.compile(r'^/[a-z]{2}[/-].*')

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(PublishedDocumentDetailViewV2, self).finalize_response(request, response, *args, **kwargs)

        if getattr(response, 'accepted_media_type', None) == 'application/json' and isinstance(response.data, dict):
            self.rewrite_frbr_uris(response.data)

        elif getattr(response, 'accepted_renderer', None) and response.accepted_renderer.media_type in ['application/xml', 'text/html']:
            self.rewrite_akn(response.data)

        return response

    def rewrite_frbr_uris(self, data):
        """ Recursively rewrite entries in data that are FRBR URIs, to ensure they
        start with /akn/
        """
        if isinstance(data, dict):
            for key, val in data.iteritems():
                if key.endswith('frbr_uri') or key == 'amending_uri' or key == 'repealing_uri':
                    if val and not val.startswith('/akn'):
                        data[key] = '/akn' + val

                if isinstance(val, dict):
                    self.rewrite_frbr_uris(val)

                elif isinstance(val, list):
                    for x in val:
                        self.rewrite_frbr_uris(x)

    def rewrite_akn(self, document):
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
