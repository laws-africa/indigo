from django.test import TestCase

from cobalt import FrbrUri
from docpipe.matchers import ExtractedCitation
from lxml import etree, html as lxml_html

from indigo.analysis.refs.works import CommonTitlesCitationMatcher


class CommonTitlesCitationMatcherTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.matcher = CommonTitlesCitationMatcher()
        self.matcher.titles = {
            "tz": {
                "Arbitration Act": "/akn/tz/act/2020/2",
                "Employment and Labour Relations Act": "/akn/tz/act/2004/6",
            }
        }
        self.frbr_uri = FrbrUri.parse("/akn/tz/judgment/zacc/2023/1")

    def test_simple_text(self):
        text = """
something about the Employment and Labour
Relations Act 2004 on broken lines
and the Arbitration Act is useful
and the Arbitration Act 2020 is good
so is the Arbitration Act, 2020 and the
and the Arbitration Act of 2020
and the Arbitration Act 1990 is not valid
but the Arbitration Act of 1990 is not valid
"""
        self.matcher.extract_text_matches(self.frbr_uri, text)

        self.assertEqual([
            ExtractedCitation(text='the Employment and Labour\nRelations Act 2004', start=17, end=61, href='/akn/tz/act/2004/6', target_id=0, prefix='\nsomething about ', suffix=' on broken lines\nand the Arbit'),
            ExtractedCitation(text='the Arbitration Act', start=82, end=101, href='/akn/tz/act/2020/2', target_id=0, prefix=' Act 2004 on broken lines\nand ', suffix=' is useful\nand the Arbitration'),
            ExtractedCitation(text='the Arbitration Act 2020', start=116, end=140, href='/akn/tz/act/2020/2', target_id=0, prefix='Arbitration Act is useful\nand ', suffix=' is good\nso is the Arbitration'),
            ExtractedCitation(text='the Arbitration Act, 2020', start=155, end=180, href='/akn/tz/act/2020/2', target_id=0, prefix='ration Act 2020 is good\nso is ', suffix=' and the\nand the Arbitration A'),
            ExtractedCitation(text='the Arbitration Act of 2020', start=193, end=220, href='/akn/tz/act/2020/2', target_id=0, prefix='tration Act, 2020 and the\nand ', suffix='\nand the Arbitration Act 1990 ')
        ], self.matcher.citations)

    def test_simple_xml(self):
        xml = """<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
<section>
    <p>something about the Employment and Labour</p>
    <p>Relations Act 2004 on broken lines</p>
    <p>and the Arbitration Act is useful</p>
    <p>and the Arbitration Act 2020 is good</p>
    <p>so is the Arbitration Act, 2020 and the</p>
    <p>and the Arbitration Act of 2020</p>
    <p>and the Arbitration Act 1990 is not valid</p>
    <p>but the Arbitration Act of 1990 is not valid</p>
</section>
</body>"""
        root = etree.fromstring(xml)
        self.matcher.markup_xml_matches(self.frbr_uri, root)

        xml = etree.tostring(root, encoding='unicode')
        self.assertEqual("""<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
<section>
    <p>something about the Employment and Labour</p>
    <p>Relations Act 2004 on broken lines</p>
    <p>and <ref href="/akn/tz/act/2020/2">the Arbitration Act</ref> is useful</p>
    <p>and <ref href="/akn/tz/act/2020/2">the Arbitration Act 2020</ref> is good</p>
    <p>so is <ref href="/akn/tz/act/2020/2">the Arbitration Act, 2020</ref> and the</p>
    <p>and <ref href="/akn/tz/act/2020/2">the Arbitration Act of 2020</ref></p>
    <p>and the Arbitration Act 1990 is not valid</p>
    <p>but the Arbitration Act of 1990 is not valid</p>
</section>
</body>""", xml)

    def test_simple_html(self):
        html = """<div>
        <p>something about the Employment and Labour</p>
        <p>Relations Act 2004 on broken lines</p>
        <p>and the Arbitration Act is useful</p>
        <p>and the Arbitration Act 2020 is good</p>
        <p>so is the Arbitration Act, 2020 and the</p>
        <p>and the Arbitration Act of 2020</p>
        <p>and the Arbitration Act 1990 is not valid</p>
        <p>but the Arbitration Act of 1990 is not valid</p>
    </div>"""
        root = lxml_html.fromstring(html)
        self.matcher.markup_html_matches(self.frbr_uri, root)

        html = etree.tostring(root, encoding='unicode')
        self.assertEqual("""<div>
        <p>something about the Employment and Labour</p>
        <p>Relations Act 2004 on broken lines</p>
        <p>and <a href="/akn/tz/act/2020/2">the Arbitration Act</a> is useful</p>
        <p>and <a href="/akn/tz/act/2020/2">the Arbitration Act 2020</a> is good</p>
        <p>so is <a href="/akn/tz/act/2020/2">the Arbitration Act, 2020</a> and the</p>
        <p>and <a href="/akn/tz/act/2020/2">the Arbitration Act of 2020</a></p>
        <p>and the Arbitration Act 1990 is not valid</p>
        <p>but the Arbitration Act of 1990 is not valid</p>
    </div>""", html)

    def test_noop_for_no_titles(self):
        self.matcher.extract_text_matches(FrbrUri.parse("/akn/xx/act/2020/1"), "hi")
        self.assertEqual([], self.matcher.citations)

    def test_brackets(self):
        self.matcher.titles = {
            "tz": {
                "Stock Theft (Prevention) Act": "/akn/tz/act/2020/2",
            }
        }
        text = """
respect of certain offences under the Stock Theft (Prevention) Act, Cap. 265 of the Revised Edition, 2002
"""
        self.matcher.extract_text_matches(self.frbr_uri, text)

        self.assertEqual([
            ExtractedCitation(text='the Stock Theft (Prevention) Act', start=35, end=67, href='/akn/tz/act/2020/2',
                              target_id=0, prefix='ect of certain offences under ',
                              suffix=', Cap. 265 of the Revised Edit')
        ], self.matcher.citations)


