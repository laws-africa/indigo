from django.template.loader import find_template, render_to_string, TemplateDoesNotExist

from cobalt.render import HTMLRenderer as CobaltHTMLRenderer


class HTMLRenderer(object):
    """ Renders an indigo_api.models.Document as HTML.
    """
    def __init__(self, cobalt_kwargs=None):
        self.cobalt_kwargs = cobalt_kwargs or {}

    def render(self, document, coverpage=True, template_name=None):
        """ Render this document to HTML.

        :param Boolean coverpage: Should a cover page be generated?
        :param str template_name: name of the django template to use (or None to find a suitable one)
        """
        # use this to render the bulk of the document with the Cobalt XSLT renderer
        renderer = self._xml_renderer(document)
        body_html = renderer.render_xml(document.document_xml)

        # find the template to use
        if not template_name:
            template_name = self._find_template(document)

        # and then render some boilerplate around it
        return render_to_string(template_name, {
            'document': document,
            'content_html': body_html,
            'renderer': renderer,
            'coverpage': coverpage,
        })

    def render_element(self, document, element):
        """ Render just an element of a document to HTML.
        """
        return self._xml_renderer(document).render(element)

    def _find_template(self, document):
        """ Return the filename of a template to use to render this document.

        This takes into account the country, type, subtype and language of the document,
        providing a number of opportunities to adjust the rendering logic.
        """
        uri = document.doc.frbr_uri
        doctype = uri.doctype

        options = []
        if uri.subtype:
            options.append('_'.join([doctype, uri.subtype, document.language, uri.country]))
            options.append('_'.join([doctype, uri.subtype, document.language]))
            options.append('_'.join([doctype, uri.subtype, uri.country]))
            options.append('_'.join([doctype, uri.country]))
            options.append('_'.join([doctype, uri.subtype]))

        options.append('_'.join([doctype, document.language, uri.country]))
        options.append('_'.join([doctype, document.language]))
        options.append('_'.join([doctype, uri.country]))
        options.append(doctype)

        options = [f + '.html' for f in options]

        for option in options:
            try:
                if find_template(option):
                    return option
            except TemplateDoesNotExist:
                pass

        raise ValueError("Couldn't find a template to use for %s. Tried: %s" % (uri, ', '.join(options)))

    def _xml_renderer(self, document):
        return CobaltHTMLRenderer(act=document.doc, **self.cobalt_kwargs)
