from django.utils import feedgenerator
from cobalt.render import HTMLRenderer
from rest_framework.reverse import reverse
from rest_framework_xml.renderers import XMLRenderer

from .serializers import NoopSerializer, DocumentSerializer


class AtomFeed(feedgenerator.Atom1Feed):
    full_feed_title = "Indigo Full Document Feed"
    summary_feed_title = "Indigo Summary Feed"

    def __init__(self, serializer=None, summary=True, next_url=None, previous_url=None, *args, **kwargs):
        self.serializer = serializer
        self.summary = summary

        # pagination
        self.next_url = next_url
        self.previous_url = previous_url

        super(AtomFeed, self).__init__(*args, **kwargs)

    def add_root_elements(self, handler):
        super(AtomFeed, self).add_root_elements(handler)

        # alternate full / summary feeds
        if self.summary:
            handler.addQuickElement("link", "", {
                "rel": "alternate",
                "title": self.full_feed_title,
                "type": "application/atom+xml",
                "href": self.feed['link'] + 'full.atom',
            })
        else:
            handler.addQuickElement("link", "", {
                "rel": "alternate",
                "title": self.summary_feed_title,
                "type": "application/atom+xml",
                "href": self.feed['link'] + 'feed.atom',
            })

        # pagination
        if self.next_url:
            handler.addQuickElement("link", "", {"rel": "next", "href": self.next_url})
        if self.previous_url:
            handler.addQuickElement("link", "", {"rel": "previous", "href": self.previous_url})

    def add_item_elements(self, handler, item):
        from indigo_api.views import document_to_html

        super(AtomFeed, self).add_item_elements(handler, item)

        handler.addQuickElement("link", "", {
            "rel": "alternate",
            "href": item['link'] + '.html',
            "type": "text/html",
            "title": "HTML",
        })

        handler.addQuickElement("link", "", {
            "rel": "alternate",
            "href": item['link'] + '.xml',
            "type": "application/xml",
            "title": "Akoma Ntoso",
        })

        if not self.summary:
            # full document body
            content = document_to_html(item['document'])
            handler.addQuickElement("content", content, {"type": "html"})

        # TODO: atom feed for this document?


class AtomRenderer(XMLRenderer):
    media_type = 'application/atom+xml'
    format = 'atom'
    # override the serializer class, we want a Document object
    serializer_class = NoopSerializer

    def render(self, data, media_type=None, renderer_context=None):
        self.serializer = DocumentSerializer(context=renderer_context)
        frbr_uri = renderer_context['kwargs']['frbr_uri']

        feed_type = renderer_context['kwargs']['feed']
        summary = feed_type != 'full'
        title = AtomFeed.summary_feed_title if summary else AtomFeed.full_feed_title

        url = reverse('published-document-detail', request=renderer_context['request'],
                      kwargs={'frbr_uri': frbr_uri[1:]})

        feed = AtomFeed(
            title="%s - %s" % (title, frbr_uri),
            feed_url=renderer_context['request'].build_absolute_uri(),
            link=url,
            description="Indigo documents under the %s FRBR URI" % frbr_uri,
            serializer=self.serializer,
            summary=summary,
            next_url=data['next'],
            previous_url=data['previous'])

        for doc in data['results']:
            self.add_item(feed, doc)

        return feed.writeString('utf-8')

    def add_item(self, feed, doc):
        url = self.serializer.get_published_url(doc)
        feed.add_item(
            unique_id=url,
            pubdate=doc.created_at,
            updateddate=doc.updated_at,
            title=doc.title,
            description=self.item_description(doc),
            link=url,
            document=doc,
            author_name='',
        )

    def item_description(self, doc):
        desc = "<h1>" + doc.title + "</h1>"

        try:
            preface = doc.doc.act.preface
            desc += "\n" + HTMLRenderer(act=doc.doc).render(preface)
        except AttributeError:
            pass

        return desc
