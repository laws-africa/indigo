from django.test import TestCase

from cobalt import FrbrUri
from docpipe.matchers import ExtractedCitation
from lxml import etree, html as lxml_html

from indigo.analysis.refs.works import AliasCitationMatcher


class AliasCitationMatcherTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.matcher = AliasCitationMatcher()
        self.matcher.aliases = {
            "ke": {
                "Penal Code": "/akn/ke/act/2009/1",
            }
        }
        self.frbr_uri = FrbrUri.parse("/akn/ke/judgment/zacc/1991/1")

    def test_simple_text(self):
        text = """
The Penal Code of Kenya
The Penalty Code of Kenya
Penal Code is cool
The Penal Code
case is penal code important
"""
        self.matcher.extract_text_matches(self.frbr_uri, text)

        self.assertEqual([
            ExtractedCitation(text='Penal Code', start=5, end=15, href='/akn/ke/act/2009/1', target_id=0,
                              prefix='\nThe ', suffix=' of Kenya\nThe Penalty Code of '),
            ExtractedCitation(text='Penal Code', start=51, end=61, href='/akn/ke/act/2009/1', target_id=0,
                              prefix='nya\nThe Penalty Code of Kenya\n', suffix=' is cool\nThe Penal Code\ncase i'),
            ExtractedCitation(text='Penal Code', start=74, end=84, href='/akn/ke/act/2009/1', target_id=0,
                              prefix=' Kenya\nPenal Code is cool\nThe ', suffix='\ncase is penal code important\n')
        ], self.matcher.citations)

    def test_simple_xml(self):
        xml = """<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
<section>
    <p>The Penal Code of Kenya</p>
    <p>The Penalty Code of Kenya</p>
    <p>Penal Code is cool</p>
    <p>The Penal Code</p>
    <p>Ignore <ref href="foo">Penal Code</ref> existing</p>
    <p>case is penal code important</p>
</section>
</body>"""
        root = etree.fromstring(xml)
        self.matcher.markup_xml_matches(self.frbr_uri, root)

        xml = etree.tostring(root, encoding='unicode')
        self.assertEqual("""<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
<section>
    <p>The <ref href="/akn/ke/act/2009/1">Penal Code</ref> of Kenya</p>
    <p>The Penalty Code of Kenya</p>
    <p><ref href="/akn/ke/act/2009/1">Penal Code</ref> is cool</p>
    <p>The <ref href="/akn/ke/act/2009/1">Penal Code</ref></p>
    <p>Ignore <ref href="foo">Penal Code</ref> existing</p>
    <p>case is penal code important</p>
</section>
</body>""", xml)

    def test_simple_html(self):
        html = """<div>
        <p>The Penal Code of Kenya</p>
        <p>The Penalty Code of Kenya</p>
        <p>Penal Code is cool</p>
        <p>The Penal Code</p>
        <p>Ignore <a href="foo">Penal Code</a> existing</p>
        <p>case is penal code important</p>
    </div>"""
        root = lxml_html.fromstring(html)
        self.matcher.markup_html_matches(self.frbr_uri, root)

        html = etree.tostring(root, encoding='unicode')
        self.assertEqual("""<div>
        <p>The <a href="/akn/ke/act/2009/1">Penal Code</a> of Kenya</p>
        <p>The Penalty Code of Kenya</p>
        <p><a href="/akn/ke/act/2009/1">Penal Code</a> is cool</p>
        <p>The <a href="/akn/ke/act/2009/1">Penal Code</a></p>
        <p>Ignore <a href="foo">Penal Code</a> existing</p>
        <p>case is penal code important</p>
    </div>""", html)

    def test_noop_for_no_aliases(self):
        self.matcher.extract_text_matches(FrbrUri.parse("/akn/xx/act/2020/1"), "hi")
        self.assertEqual([], self.matcher.citations)

    def test_aliases_with_quotes_and_regex_punctuation(self):
        aliases = ["King's Regulation", 'The "Blue" Act', 'King\'s "Blue" Act', 'A.B Code']
        alias_map = {alias: "/akn/ke/act/2009/1" for alias in aliases}
        self.matcher.aliases = {"ke": alias_map}

        self.matcher.extract_text_matches(self.frbr_uri, ' | '.join(aliases) + ' | A-B Code')
        self.assertEqual(aliases, [citation.text for citation in self.matcher.citations])

        for markup, marker in (("xml", "ref"), ("html", "a")):
            with self.subTest(markup=markup):
                if markup == "xml":
                    root = etree.fromstring('<body xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><p/></body>')
                    paragraph = root[0]
                else:
                    root = lxml_html.fromstring('<div><p/></div>')
                    paragraph = root[0]
                paragraph.text = ' | '.join(aliases) + ' | A-B Code'

                self.matcher.aliases = {"ke": alias_map}
                getattr(self.matcher, f'markup_{markup}_matches')(self.frbr_uri, root)

                self.assertEqual(aliases, [node.text for node in root.iter() if etree.QName(node).localname == marker])
                self.assertIn('A-B Code', ''.join(root.itertext()))
