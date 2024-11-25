from django.test import TestCase
from lxml import etree

from indigo.analysis.sentence_caser import BaseSentenceCaser
from indigo_api.models import Document, Work
from indigo_api.tests.fixtures import document_fixture


class SentenceCaserTestCase(TestCase):
    fixtures = ['languages_data', 'countries']

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/1991/1')
        self.sentence_caser = BaseSentenceCaser()
        self.sentence_caser.terms = ['Tâx', 'táxation', 'in the Höme']
        self.maxDiff = None

    def test_sentence_case_headings_in_document(self):
        document = Document(
            work=self.work,
            language_id=1,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_0">
          <num>0</num>
          <heading><i> TAXATION </i>IN<sup><authorialNote marker="1" placement="bottom" eId="sec_0__authorialNote_1"><p eId="sec_0__authorialNote_1__p_1">OR ON</p></authorialNote></sup> THE HOME<sup><authorialNote marker="1A" placement="bottom" eId="sec_0__authorialNote_2"><p eId="sec_0__authorialNote_2__p_1">FN</p></authorialNote></sup></heading>
          <content>
            <p eId="sec_0__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_1">
          <num>1</num>
          <heading><i>HELLO</i> NO TAXATION <i>WITHOUT REPRESENTATION</i> <b>(OTHER STUFF)</b></heading>
          <content>
            <p eId="sec_1__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_1A">
          <num>1A</num>
          <heading><i> </i>HELLO NO TAXATION <i>WITHOUT REPRESENTATION</i> <b>(OTHER STUFF)</b></heading>
          <content>
            <p eId="sec_1A__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_2">
          <num>2</num>
          <heading>TAXATION AND TAX, AND TAXONOMIES TOO</heading>
          <content>
            <p eId="sec_2__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_2A">
          <num>2A</num>
          <heading>TAXONOMIES ALL ALONE</heading>
          <content>
            <p eId="sec_2A__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_3">
          <num>3</num>
          <heading>TAXATION <i>IN THE HOME</i></heading>
          <content>
            <p eId="sec_3__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_4">
          <num>4</num>
          <heading><i> TAXATION </i>IN THE HOME<sup><authorialNote marker="1" placement="bottom" eId="sec_4__authorialNote_1"><p eId="sec_4__authorialNote_1__p_1">FN</p></authorialNote></sup></heading>
          <content>
            <p eId="sec_4__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_5">
          <num>5</num>
          <heading>DOUBLE <b>TAXATION</b></heading>
          <content>
            <p eId="sec_5__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_6">
          <num>6</num>
          <heading>SINGLE <i>TAXATION</i></heading>
          <content>
            <p eId="sec_6__p_1">Text</p>
          </content>
        </section>
                """
            )
        )

        expected = Document(
            work=self.work,
            document_xml=document_fixture(
                xml="""
        <section eId="sec_0">
          <num>0</num>
          <heading><i>Táxation </i>in<sup><authorialNote marker="1" placement="bottom" eId="sec_0__authorialNote_1"><p eId="sec_0__authorialNote_1__p_1">OR ON</p></authorialNote></sup> the home<sup><authorialNote marker="1A" placement="bottom" eId="sec_0__authorialNote_2"><p eId="sec_0__authorialNote_2__p_1">FN</p></authorialNote></sup></heading>
          <content>
            <p eId="sec_0__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_1">
          <num>1</num>
          <heading><i>Hello</i> no táxation <i>without representation</i> <b>(other stuff)</b></heading>
          <content>
            <p eId="sec_1__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_1A">
          <num>1A</num>
          <heading><i> </i>Hello no táxation <i>without representation</i> <b>(other stuff)</b></heading>
          <content>
            <p eId="sec_1A__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_2">
          <num>2</num>
          <heading>Táxation and Tâx, and taxonomies too</heading>
          <content>
            <p eId="sec_2__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_2A">
          <num>2A</num>
          <heading>Taxonomies all alone</heading>
          <content>
            <p eId="sec_2A__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_3">
          <num>3</num>
          <heading>Táxation <i>in the Höme</i></heading>
          <content>
            <p eId="sec_3__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_4">
          <num>4</num>
          <heading><i>Táxation </i>in the Höme<sup><authorialNote marker="1" placement="bottom" eId="sec_4__authorialNote_1"><p eId="sec_4__authorialNote_1__p_1">FN</p></authorialNote></sup></heading>
          <content>
            <p eId="sec_4__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_5">
          <num>5</num>
          <heading>Double <b>táxation</b></heading>
          <content>
            <p eId="sec_5__p_1">Text</p>
          </content>
        </section>
        <section eId="sec_6">
          <num>6</num>
          <heading>Single <i>táxation</i></heading>
          <content>
            <p eId="sec_6__p_1">Text</p>
          </content>
        </section>
                """
            )
        )

        self.sentence_caser.sentence_case_headings_in_document(document)
        root = etree.fromstring(expected.content.encode('utf-8'))
        expected.content = etree.tostring(root, encoding='utf-8').decode('utf-8')
        self.assertEqual(expected.content, document.content)
