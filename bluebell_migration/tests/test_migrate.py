from django.test import TestCase

from lxml import etree
from bluebell_migration.migrate import SlawToBluebell, pretty_c14n


class SlawToBluebellTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.migration = SlawToBluebell()

    def test_table_br_to_p(self):
        xml = """<td xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0"><p>
  start
  <b>
    bold
    <i>italics <br/> br tail <sup>tail sup</sup></i>
    ital <sup>mixed tail</sup> tail
  </b>
  bold tail
</p></td>
"""
        xml = self.migration.unpretty(xml)
        xml = etree.fromstring(xml)

        self.migration.table_br_to_p(xml)

        xml = pretty_c14n(etree.tostring(xml, encoding='unicode'))
        self.assertMultiLineEqual("""<td xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <p>
  start
  <b>
    bold
    <i>italics </i></b></p>
  <p><b><i> br tail <sup>tail sup</sup></i>
    ital <sup>mixed tail</sup> tail
  </b>
  bold tail
</p>
</td>
""".strip(), xml.strip())
