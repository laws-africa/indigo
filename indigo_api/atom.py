from django.utils import feedgenerator
from rest_framework.reverse import reverse
from rest_framework_xml.renderers import XMLRenderer

from .serializers import NoopSerializer, DocumentSerializer
from .renderers import HTMLRenderer


class AtomFeed(feedgenerator.Atom1Feed):
    # how many items in the full feed summary? This should be pretty small, these documents
    # will be big
    full_feed_page_size = 10
    full_feed_title = "Indigo Full Document Feed"
    summary_feed_title = "Indigo Summary Feed"
    metadata_ns = "http://indigo.code4sa.org/ns/metadata"

    def __init__(self, serializer=None, summary=True, next_url=None, previous_url=None, *args, **kwargs):
        self.serializer = serializer
        self.summary = summary

        # pagination
        self.next_url = next_url
        self.previous_url = previous_url

        super(AtomFeed, self).__init__(*args, **kwargs)

    def root_attributes(self):
        attrs = super(AtomFeed, self).root_attributes()
        attrs['xmlns:im'] = self.metadata_ns
        return attrs

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
                "href": self.feed['link'] + 'summary.atom',
            })

        # pagination
        if self.next_url:
            handler.addQuickElement("link", "", {"rel": "next", "href": self.next_url})
        if self.previous_url:
            handler.addQuickElement("link", "", {"rel": "previous", "href": self.previous_url})

    def add_item_elements(self, handler, item):
        super(AtomFeed, self).add_item_elements(handler, item)

        doc = item['document']

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

        handler.addQuickElement("link", "", {
            "rel": "alternate",
            "href": item['link'] + '.json',
            "type": "application/json",
            "title": "JSON",
        })

        if not doc.stub and not self.summary:
            # full document body
            content = doc.to_html()
            handler.addQuickElement("content", content, {"type": "html"})

        # metadata
        handler.addQuickElement("im:frbr-uri", doc.frbr_uri)
        handler.addQuickElement("im:country", doc.country)
        if doc.locality:
            handler.addQuickElement("im:locality", doc.locality)
        handler.addQuickElement("im:nature", doc.nature)
        if doc.subtype:
            handler.addQuickElement("im:subtype", doc.subtype)
        handler.addQuickElement("im:year", doc.year)
        handler.addQuickElement("im:number", doc.number)

        if doc.expression_date:
            handler.addQuickElement("im:expression-date", doc.expression_date.isoformat())
        if doc.assent_date:
            handler.addQuickElement("im:assent-date", doc.assent_date.isoformat())
        if doc.commencement_date:
            handler.addQuickElement("im:commencement-date", doc.commencement_date.isoformat())

        if doc.publication_date:
            handler.addQuickElement("im:publication-date", doc.publication_date.isoformat())
        if doc.publication_name:
            handler.addQuickElement("im:publication-name", doc.publication_name)
        if doc.publication_number:
            handler.addQuickElement("im:publication-number", doc.publication_number)

    def item_description(self, doc):
        desc = doc.title
        if doc.expression_date:
            desc += " as at " + doc.expression_date.isoformat()
        desc = "<h1>" + desc + "</h1>"

        if not doc.stub:
            try:
                preface = doc.doc.act.preface
                desc += "\n" + HTMLRenderer().render(doc, preface)
            except AttributeError:
                pass

        return desc


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
            description=feed.item_description(doc),
            link=url,
            document=doc,
            author_name='',
        )
