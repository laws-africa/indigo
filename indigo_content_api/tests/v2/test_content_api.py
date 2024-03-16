import json
import tempfile
from datetime import date

from mock import patch
from django.test.utils import override_settings
from django.conf import settings
from sass_processor.processor import SassProcessor
from rest_framework.test import APITestCase

from indigo_api.exporters import PDFExporter
from indigo_api.models import Country


# Ensure the processor runs during tests. It doesn't run when DEBUG=False (ie. during testing),
# but during testing we haven't compiled assets
SassProcessor.processor_enabled = True


class ContentAPIV2TestMixin:
    api_path = '/api/v2'
    api_host = 'testserver'

    def setUp(self):
        self.client.login(username='api-user@example.com', password='password')

        # override settings to set custom properties
        self.old_work_properties = settings.INDIGO['WORK_PROPERTIES']
        settings.INDIGO['WORK_PROPERTIES'] = {
            'za': {
                'cap': 'Chapter',
                'bad': 'Should be ignored',
            }
        }
        self.maxDiff = None

    def tearDown(self):
        settings.INDIGO['WORK_PROPERTIES'] = self.old_work_properties

    def test_published_json_perms(self):
        self.client.logout()
        self.client.login(username='email@example.com', password='password')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10')
        self.assertEqual(response.status_code, 403)

    def test_published_json(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/za/act/2014/10')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/za/act/2014/10')

    def test_published_numbered_title(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['numbered_title'], 'Act 10 of 2014')

    def test_published_type_name(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['type_name'], 'Act')

    def test_published_xml(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/xml')
        self.assertIn('<akomaNtoso', response.content.decode('utf-8'))

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/xml')
        self.assertIn('<akomaNtoso', response.content.decode('utf-8'))

    @patch.object(PDFExporter, 'render', return_value='pdf-content')
    def test_published_pdf(self, mock):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/pdf')
        self.assertIn('pdf-content', response.content.decode('utf-8'))

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/pdf')
        self.assertIn('pdf-content', response.content.decode('utf-8'))

    def test_published_epub(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.epub')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/epub+zip')
        self.assertTrue(response.content.startswith(b'PK'))

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.epub')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/epub+zip')
        self.assertTrue(response.content.startswith(b'PK'))

    def test_published_html(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertIn('<span', response.content.decode('utf-8'))

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertNotIn('<body', response.content.decode('utf-8'))
        self.assertIn('<span', response.content.decode('utf-8'))

    def test_published_html_standalone(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.html?standalone=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertIn('<body  class="standalone"', response.content.decode('utf-8'))
        self.assertIn('class="colophon"', response.content.decode('utf-8'))
        self.assertIn('class="toc"', response.content.decode('utf-8'))

    def test_published_listing(self):
        response = self.client.get(self.api_path + '/akn/za/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(len(response.data['results']), 7)

        response = self.client.get(self.api_path + '/akn/za/act/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(len(response.data['results']), 7)

        response = self.client.get(self.api_path + '/akn/za/act/2014')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(len(response.data['results']), 1)

    def test_published_listing_filters(self):
        response = self.client.get(self.api_path + '/akn/za/', {'updated_at__lte': '2015-02-20T00:00:00Z'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(['/akn/za/act/1880/1', '/akn/za/act/2014/10', '/akn/za/act/2017/17'], [r["frbr_uri"] for r in response.data['results']])

        response = self.client.get(self.api_path + '/akn/za/', {'updated_at__gte': '2015-06-01T00:00:00Z'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(['/akn/za/act/2001/8',
                          '/akn/za/act/2010/1',
                          '/akn/za/act/2016/16',
                          '/akn/za/act/2017/17',
                          '/akn/za/act/2023/1'],
                         [r["frbr_uri"] for r in response.data['results']])

    @patch.object(PDFExporter, 'render', return_value='pdf-content')
    def test_published_listing_pdf(self, mock):
        response = self.client.get(self.api_path + '/akn/za/act.pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/pdf')
        # we don't support rendering more than one PDF (see PDFRenderer.render)
        self.assertEqual('', response.content.decode('utf-8'))

    def test_published_listing_pagination(self):
        response = self.client.get(self.api_path + '/akn/za/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(set(response.data.keys()), set(['next', 'previous', 'count', 'results', 'links']))

    def test_published_listing_html_404(self):
        # explicitly asking for html is bad
        response = self.client.get(self.api_path + '/akn/za/act.html')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.accepted_media_type, 'text/html')

    def test_published_listing_pdf_404(self):
        response = self.client.get(self.api_path + '/akn/za/act/bad.pdf')
        self.assertEqual(response.status_code, 404)

    def test_published_listing_epub_404(self):
        response = self.client.get(self.api_path + '/akn/za/act/bad.epub')
        self.assertEqual(response.status_code, 404)

    def test_published_missing(self):
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22.html').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22.xml').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22.json').status_code, 404)

        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22/eng').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22/eng.html').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22/eng.xml').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/22/eng.json').status_code, 404)

    def test_published_wrong_language(self):
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2014/10/fre').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2014/10/fre.html').status_code, 404)

    def test_published_listing_missing(self):
        self.assertEqual(self.client.get(self.api_path + '/akn/za/act/2999/').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/zm/').status_code, 404)
        self.assertEqual(self.client.get(self.api_path + '/akn/za-foo/').status_code, 404)

    def test_bad_toc_url(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/toc.json')
        self.assertEqual(response.status_code, 404)
        response = self.client.get(self.api_path + '/akn/za/act/by-law/2014/toc.json')
        self.assertEqual(response.status_code, 404)

    def test_published_toc(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng/toc.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['toc'], [
            {'id': 'sec_1', 'type': 'section', 'num': '1.', 'component': 'main',
             'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng/!main~sec_1',
             'title': 'Section 1.', 'basic_unit': True, 'children': [], 'heading': None}])

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/toc.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['toc'], [
            {'id': 'sec_1', 'type': 'section', 'num': '1.', 'component': 'main',
             'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng/!main~sec_1',
             'title': 'Section 1.', 'basic_unit': True, 'children': [], 'heading': None}])

        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng/toc.json')
        self.assertEqual([{
            'type': 'section',
            'component': 'main',
            'title': '1. Foo',
            'children': [{
                'type': 'subsection',
                'component': 'main',
                'title': 'Subsection',
                'children': [],
                'basic_unit': False,
                'id': 'sec_1.subsection-0',
                'num': None,
                'heading': None,
                'url': f'http://{self.api_host}{self.api_path}/akn/za/act/2010/1/eng/!main~sec_1.subsection-0',
            }],
            'basic_unit': True,
            'heading': 'Foo',
            'num': '1.',
            'id': 'sec_1',
            'url': f'http://{self.api_host}{self.api_path}/akn/za/act/2010/1/eng/!main~sec_1'}],
                         response.data['toc'])
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/toc.json')
        self.assertEqual([{
            'type': 'section',
            'component': 'main',
            'title': '1. Foo',
            'children': [{
                'type': 'subsection',
                'component': 'main',
                'title': 'Subsection',
                'children': [],
                'basic_unit': False,
                'id': 'sec_1.subsection-0',
                'num': None,
                'heading': None,
                'url': f'http://{self.api_host}{self.api_path}/akn/za/act/2010/1/eng/!main~sec_1.subsection-0',
            }],
            'basic_unit': True,
            'heading': 'Foo',
            'num': '1.',
            'id': 'sec_1',
            'url': f'http://{self.api_host}{self.api_path}/akn/za/act/2010/1/eng/!main~sec_1'}],
                         response.data['toc'])

    def test_published_toc_sections_with_headings(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng/toc.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['toc'], [
            {
                'id': 'sec_1',
                'type': 'section',
                'num': '1.',
                'component': 'main',
                'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng/!main~sec_1',
                'heading': 'Foo',
                'title': '1. Foo',
                'basic_unit': True,
                'children': [
                    {
                        'component': 'main',
                        'id': 'sec_1.subsection-0',
                        'title': 'Subsection',
                        'type': 'subsection',
                        'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng/!main~sec_1.subsection-0',
                        'basic_unit': False,
                        'children': [],
                        'num': None,
                        'heading': None,
                    }
                ],
            }
        ])

    def test_published_toc_uses_expression_date_in_urls(self):
        # use @2014-02-12
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng@2014-02-12/toc.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['toc'], [
            {'id': 'sec_1', 'type': 'section', 'num': '1.', 'component': 'main',
             'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng@2014-02-12/!main~sec_1',
             'title': 'Section 1.', 'basic_unit': True, 'children': [], 'heading': None}])

        # use :2014-02-12
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng:2014-02-12/toc.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['toc'], [
            {'id': 'sec_1', 'type': 'section', 'num': '1.',
             'component': 'main',
             'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng:2014-02-12/!main~sec_1',
             'title': 'Section 1.', 'basic_unit': True, 'children': [], 'heading': None}])

    def test_published_portion(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng/!main~sec_1.xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/xml')
        self.assertEqual(response.content.decode('utf-8'), '''<section xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0" eId="sec_1"><num>1.</num>
        <content>
          <p>tester😀</p><p/><p><img src="media/test-image.png"/></p>
        </content>
      </section>
    
''')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng/!main~sec_1.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertEqual(response.content.decode('utf-8'), '''<section class="akn-section" id="sec_1" data-eId="sec_1"><h3>1. </h3><span class="akn-content">
          <span class="akn-p">tester😀</span><span class="akn-p"> </span><span class="akn-p"><img class="akn-img" data-src="media/test-image.png" src="media/test-image.png"/></span>
        </span></section>''')

    def test_at_expression_date(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng@2011-01-01.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['expression_date'], '2011-01-01')

        # doesn't exist
        response = self.client.get(self.api_path + '/akn/za/act/2011/5/eng@2099-01-01.json')
        self.assertEqual(response.status_code, 404)

    def test_before_expression_date(self):
        # at or before 2015-01-01
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng:2015-01-01.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['expression_date'], '2012-02-02')

        # at or before 2012-01-01
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng:2012-01-01.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['expression_date'], '2011-01-01')

        # doesn't exist
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng:2009-01-01.json')
        self.assertEqual(response.status_code, 404)

    def test_latest_expression(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['expression_date'], '2012-02-02')

    def test_latest_expression_in_listing(self):
        # a listing should only include the most recent expression of a document
        # with different expression dates
        response = self.client.get(self.api_path + '/akn/za/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')

        docs = [d for d in response.data['results'] if d['frbr_uri'] == '/za/act/2010/1']
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['expression_date'], '2012-02-02')

    def test_earliest_expression(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng@.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['expression_date'], '2011-01-01')

    def test_published_points_in_time(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng@.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/za/act/2010/1')
        self.assertEqual(response.data['points_in_time'], [
            {
                'date': '2011-01-01',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng@2011-01-01',
                    'expression_frbr_uri': '/za/act/2010/1/eng@2011-01-01',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2011-01-01',
                }]
            },
            {
                'date': '2012-02-02',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng@2012-02-02',
                    'expression_frbr_uri': '/za/act/2010/1/eng@2012-02-02',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2012-02-02',
                }]
            }
        ])

    def test_published_repealed(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['repeal'], {
            'date': '2014-02-12',
            'repealing_uri': '/za/act/2014/10',
            'repealing_title': 'Water Act',
        })

    def test_commenced(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['commenced'], True)
        self.assertEqual(response.data['commencement_date'], '2010-06-01')
        self.assertEqual([dict(x) for x in response.data['commencements']], [{
            'commencing_title': None,
            'commencing_frbr_uri': None,
            'date': '2010-06-01',
            'provisions': [],
            'main': True,
            'note': 'A note',
            'all_provisions': True,
        }])

    def test_published_alternate_links(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')

        links = response.data['links']
        links.sort(key=lambda k: k['title'])

        self.assertEqual(links, [
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng.xml',
             'mediaType': 'application/xml', 'rel': 'alternate', 'title': 'Akoma Ntoso'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng.html', 'mediaType': 'text/html',
             'rel': 'alternate', 'title': 'HTML'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng/media.json',
             'mediaType': 'application/json', 'rel': 'media', 'title': 'Media'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng.pdf',
             'mediaType': 'application/pdf', 'rel': 'alternate', 'title': 'PDF'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng.html?standalone=1',
             'mediaType': 'text/html', 'rel': 'alternate', 'title': 'Standalone HTML'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng/toc.json',
             'mediaType': 'application/json', 'rel': 'toc', 'title': 'Table of Contents'},
            {'href': 'http://' + self.api_host + self.api_path + '/akn/za/act/2001/8/eng.epub',
             'mediaType': 'application/epub+zip', 'rel': 'alternate', 'title': 'ePUB'},
        ])

    def test_published_media_attachments(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng.json')
        self.assertEqual(response.status_code, 200)
        id = 4  # we know this is document 4

        # should be empty
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        # should not exist
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media/test.png')
        self.assertEqual(response.status_code, 404)

        # create a doc with an attachment
        self.client.login(username='email@example.com', password='password')
        self.upload_attachment(id)

        # should have one item
        self.client.login(username='api-user@example.com', password='password')
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

        # now should exist
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media/test.png')
        self.assertEqual(response.status_code, 200)

        # 403 for anonymous
        self.client.logout()
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media/test.png')
        self.assertEqual(response.status_code, 403)

        # even for a non-existent one
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng/media/bad.png')
        self.assertEqual(response.status_code, 403)

    def upload_attachment(self, doc_id):
        tmp_file = tempfile.NamedTemporaryFile(suffix='.png')
        # this is the smallest possible transparent png
        # see https://github.com/mathiasbynens/small
        tmp_file.write(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        tmp_file.seek(0)
        response = self.client.post('/api/documents/%s/attachments' % doc_id,
                                    {'file': tmp_file, 'filename': 'test.png'}, format='multipart')
        self.assertEqual(response.status_code, 201)

    def test_published_zipfile(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng.zip')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/zip')

    def test_published_zipfile_many(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001.zip')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/zip')

    def test_published_frbr_urls(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng@2014-02-12.json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['url'], 'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng@2014-02-12')

        links = {link['rel']: link['href'] for link in response.data['links']}
        self.assertEqual(links['toc'],
                     'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng@2014-02-12/toc.json')
        self.assertEqual(links['media'],
                     'http://' + self.api_host + self.api_path + '/akn/za/act/2014/10/eng@2014-02-12/media.json')

    def test_published_publication_document_trusted_url(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1/eng@1880-10-12.json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['publication_document']['url'], 'https://example.com/foo.pdf')

    def test_published_publication_document(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng@2014-02-12.json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.data['publication_document']['url'],
                     f'http://{self.api_host}{self.api_path}/akn/za/act/2014/10/media/publication/za-act-2014-10-publication-document.pdf')

    def test_published_work_before_1900(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1.html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'text/html')
        self.assertNotIn('<akomaNtoso', response.content.decode('utf-8'))
        self.assertIn('<span', response.content.decode('utf-8'))

    def test_taxonomies(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1.json')
        self.assertEqual(response.status_code, 200)

        # sort them so we can compare them easily
        taxonomies = sorted(json.loads(json.dumps(response.data['taxonomies'])), key=lambda t: t['vocabulary'])
        for tax in taxonomies:
            tax['topics'].sort(key=lambda t: (t['level_1'], t['level_2']))

        self.assertEqual([{
            "vocabulary": "",
            "title": "Third Party Taxonomy",
            "topics": [
                {
                    "level_1": "Fun stuff",
                    "level_2": None,
                },
            ],
        }, {
            "vocabulary": "lawsafrica-subjects",
            "title": "Laws.Africa Subject Taxonomy",
            "topics": [
                {
                    "level_1": "Money and Business",
                    "level_2": "Banking"
                },
            ],
        }], taxonomies)

    def test_as_at_date(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1.json')
        self.assertEqual(response.data['as_at_date'], "2019-01-01")

    def test_stub(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['stub'])

    def test_custom_properties(self):
        response = self.client.get(self.api_path + '/akn/za/act/1880/1.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['custom_properties'], [])

        response = self.client.get(self.api_path + '/akn/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([{
            'key': 'cap',
            'label': 'Chapter',
            'value': '52',
        }], response.data['custom_properties'])

    def test_parent_work(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data['parent_work'])

    def test_as_at_date_not_max_expression_date(self):
        """ The as-at date for an individual work with points in time after the as-at date,
        is still the as-at date.
        It just won't be used on the coverpage for expressions that are later.
        """
        za = Country.for_code('za')
        za.settings.as_at_date = date(2009, 1, 1)
        za.settings.save()

        response = self.client.get(self.api_path + '/akn/za/act/2010/1.json')
        self.assertEqual(response.data['as_at_date'], "2009-01-01")

    def test_published_json(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2014/10')

    def test_latest_expression_in_listing(self):
        # a listing should only include the most recent expression of a document
        # with different expression dates
        response = self.client.get(self.api_path + '/akn/za/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')

        docs = [d for d in response.data['results'] if d['frbr_uri'] == '/akn/za/act/2010/1']
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['expression_date'], '2012-02-02')

    def test_published_points_in_time(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1/eng@.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['frbr_uri'], '/akn/za/act/2010/1')
        self.assertEqual(response.data['points_in_time'], [
            {
                'date': '2011-01-01',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng@2011-01-01',
                    'expression_frbr_uri': '/akn/za/act/2010/1/eng@2011-01-01',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2011-01-01',
                }]
            },
            {
                'date': '2012-02-02',
                'expressions': [{
                    'url': 'http://' + self.api_host + self.api_path + '/akn/za/act/2010/1/eng@2012-02-02',
                    'expression_frbr_uri': '/akn/za/act/2010/1/eng@2012-02-02',
                    'language': 'eng',
                    'title': 'Act with amendments',
                    'expression_date': '2012-02-02',
                }]
            }
        ])

    def test_published_repealed(self):
        response = self.client.get(self.api_path + '/akn/za/act/2001/8/eng.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.accepted_media_type, 'application/json')
        self.assertEqual(response.data['repeal'], {
            'date': '2014-02-12',
            'repealing_uri': '/akn/za/act/2014/10',
            'repealing_title': 'Water Act',
        })

    def test_published_html_akn_prefixed(self):
        response = self.client.get(self.api_path + '/akn/za/act/2010/1.html')
        self.assertNotIn('/resolver/resolve/za', response.content.decode('utf-8'))
        self.assertIn('/resolver/resolve/akn/za', response.content.decode('utf-8'))

    def test_published_publication_document(self):
        response = self.client.get(self.api_path + '/akn/za/act/2014/10/eng@2014-02-12.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data['publication_document']['url'],
            f'http://{self.api_host}{self.api_path}/akn/za/act/2014/10/media/publication/za-act-2014-10-publication-document.pdf')


# Disable pipeline storage - see https://github.com/cyberdelia/django-pipeline/issues/277
@override_settings(STATICFILES_STORAGE='pipeline.storage.PipelineStorage', PIPELINE_ENABLED=False)
class ContentAPIV2Test(ContentAPIV2TestMixin, APITestCase):
    fixtures = ['languages_data', 'countries', 'user', 'editor', 'taxonomies', 'taxonomy_topics', 'work', 'published', 'colophon', 'attachments',
                'commencements']
