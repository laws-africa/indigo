# coding=utf-8
from django.test import TestCase

from indigo_api.data_migrations import AKNeId


class MigrationTestCase(TestCase):
    maxDiff = None

    def test_migration(self):
        migration = AKNeId()

        input = """
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome"/>
          <FRBRalias value="Aerodromes"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2020-03-17" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="2042" name="Eastern Cape Provincial Gazette" showAs="Eastern Cape Provincial Gazette" date="2009-02-27"/>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
        <TLCTerm id="term-aerodrome" showAs="aerodrome" href="/ontology/term/this.eng.aerodrome"/>
        <TLCTerm id="term-taxiway" showAs="taxiway" href="/ontology/term/this.eng.taxiway"/>
      </references>
    </meta>
    <preface>
      <longTitle>
        <p>To provide for air quality management and reasonable measures to prevent air pollution; to provide for the designation of the air quality officer; to provide for the establishment of local emissions norms and standards, and the promulgation of smoke control zones; to prohibit smoke emissions from dwellings and other premises; to provide for installation and operation of fuel burning equipment and obscuration measuring equipment, monitoring and sampling; to prohibit the emissions caused by dust, open burning and the burning of material; to prohibit dark smoke from compression ignition powered vehicles and provide for stopping, inspection and testing procedures; to prohibit emissions that cause a nuisance; to repeal the City of Cape Town: Air Quality Management By-law, 2010 and to provide for matters connected therewith;.</p>
      </longTitle>
    </preface>
    <preamble>
      <p>WHEREAS everyone has the constitutional right to an environment that is not harmful to their health or well-being;</p>
      <p>WHEREAS everyone has the constitutional right to have the environment protected, for the benefit of present and future generations, through reasonable legislative and other measures that–</p>
      <p>a) Prevent pollution and ecological degradation;</p>
      <p>b) Promote conservation; and</p>
      <p>c) Secure ecologically sustainable development and use of natural resources while promoting justifiable economic and social development;</p>
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section id="section-1">
        <hcontainer id="section-1.hcontainer_0">
          <content>
            <p>text</p>
          </content>
        </hcontainer>
      </section>
      <section id="section-2">
        <num>2.</num>
        <heading>Powers of the caretaker</heading>
        <subsection id="section-2.1">
          <num>(1)</num>
          <content>
            <blockList id="section-2.1.list0">
              <listIntroduction>The Caretaker may-</listIntroduction>
              <item id="section-2.1.list0.a">
                <num>(a)</num>
                <p>prohibit any person who fails to pay an amount in respect of any facility on the aerodrome of which he makes use after such charges have become payable, to make use of any facility of the aerodrome:</p>
              </item>
              <item id="section-2.1.list0.b">
                <num>(b)</num>
                <p>should he for any reason deem it necessary at any time, for such period as he may determine, prohibit or limit the admission of people or vehicles, or both, to the aerodrome or to any particular area thereof;</p>
              </item>
              <item id="section-2.1.list0.c">
                <num>(c)</num>
                <p>order any person who, in his view, acts in such a way as to cause a nuisance or detrimentally affect the good management of the aerodrome to leave the aerodrome and if such person refuses to obey his order, take steps to have such person removed;</p>
              </item>
            </blockList>
          </content>
        </subsection>
        <subsection id="section-2.2.1">
          <num>2.1</num>
          <content>
            <p>Neither the Municipality nor the Caretaker must be liable for any loss or damage, whether directly or indirectly, owing to or arising from any act which the Caretaker performed or caused to be performed in terms of subsection (1)(d) or (e).</p>
          </content>
        </subsection>
      </section>
      <chapter id="chapter-6">
        <num>6</num>
        <part id="chapter-6.part-2">
          <num>2</num>
          <section id="section-3">
            <content>
              <p>The third section.</p>
            </content>
          </section>
          <section id="section-3A">
            <num>3A.</num>
            <subsection id="section-3A.1">
              <num>(1)</num>
              <content>
                <p>Section 3A, subsection (1).</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <part id="part-3">
        <num>3</num>
        <chapter id="part-3.chapter-1">
          <num>1</num>
          <section id="section-4">
            <content>
              <p>The fourth section.</p>
            </content>
          </section>
        </chapter>
      </part>
    </body>
  </act>
</akomaNtoso>"""
        output = migration.update_xml(input)
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome"/>
          <FRBRalias value="Aerodromes"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2009-02-27" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27/main"/>
          <FRBRuri value="/akn/za-ec443/act/by-law/2009/aerodrome/eng@2009-02-27"/>
          <FRBRdate date="2020-03-17" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="2042" name="Eastern Cape Provincial Gazette" showAs="Eastern Cape Provincial Gazette" date="2009-02-27"/>
      <references source="#this">
        <TLCOrganization href="https://github.com/longhotsummer/slaw" showAs="Slaw" eId="slaw"/>
        <TLCOrganization href="/ontology/organization/za/council" showAs="Council" eId="council"/>
        <TLCTerm showAs="aerodrome" href="/ontology/term/this.eng.aerodrome" eId="term-aerodrome"/>
        <TLCTerm showAs="taxiway" href="/ontology/term/this.eng.taxiway" eId="term-taxiway"/>
      </references>
    </meta>
    <preface>
      <longTitle>
        <p>To provide for air quality management and reasonable measures to prevent air pollution; to provide for the designation of the air quality officer; to provide for the establishment of local emissions norms and standards, and the promulgation of smoke control zones; to prohibit smoke emissions from dwellings and other premises; to provide for installation and operation of fuel burning equipment and obscuration measuring equipment, monitoring and sampling; to prohibit the emissions caused by dust, open burning and the burning of material; to prohibit dark smoke from compression ignition powered vehicles and provide for stopping, inspection and testing procedures; to prohibit emissions that cause a nuisance; to repeal the City of Cape Town: Air Quality Management By-law, 2010 and to provide for matters connected therewith;.</p>
      </longTitle>
    </preface>
    <preamble>
      <p>WHEREAS everyone has the constitutional right to an environment that is not harmful to their health or well-being;</p>
      <p>WHEREAS everyone has the constitutional right to have the environment protected, for the benefit of present and future generations, through reasonable legislative and other measures that–</p>
      <p>a) Prevent pollution and ecological degradation;</p>
      <p>b) Promote conservation; and</p>
      <p>c) Secure ecologically sustainable development and use of natural resources while promoting justifiable economic and social development;</p>
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/akn/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <section eId="sec_1">
        <hcontainer eId="sec_1__hcontainer_0">
          <content>
            <p>text</p>
          </content>
        </hcontainer>
      </section>
      <section eId="sec_2">
        <num>2.</num>
        <heading>Powers of the caretaker</heading>
        <subsection eId="sec_2__subsec_1">
          <num>(1)</num>
          <content>
            <blockList eId="sec_2__subsec_1__list_0">
              <listIntroduction>The Caretaker may-</listIntroduction>
              <item eId="sec_2__subsec_1__list_0__item_a">
                <num>(a)</num>
                <p>prohibit any person who fails to pay an amount in respect of any facility on the aerodrome of which he makes use after such charges have become payable, to make use of any facility of the aerodrome:</p>
              </item>
              <item eId="sec_2__subsec_1__list_0__item_b">
                <num>(b)</num>
                <p>should he for any reason deem it necessary at any time, for such period as he may determine, prohibit or limit the admission of people or vehicles, or both, to the aerodrome or to any particular area thereof;</p>
              </item>
              <item eId="sec_2__subsec_1__list_0__item_c">
                <num>(c)</num>
                <p>order any person who, in his view, acts in such a way as to cause a nuisance or detrimentally affect the good management of the aerodrome to leave the aerodrome and if such person refuses to obey his order, take steps to have such person removed;</p>
              </item>
            </blockList>
          </content>
        </subsection>
        <subsection eId="sec_2__subsec_2-1">
          <num>2.1</num>
          <content>
            <p>Neither the Municipality nor the Caretaker must be liable for any loss or damage, whether directly or indirectly, owing to or arising from any act which the Caretaker performed or caused to be performed in terms of subsection (1)(d) or (e).</p>
          </content>
        </subsection>
      </section>
      <chapter eId="chp_6">
        <num>6</num>
        <part eId="chp_6__part_2">
          <num>2</num>
          <section eId="sec_3">
            <content>
              <p>The third section.</p>
            </content>
          </section>
          <section eId="sec_3A">
            <num>3A.</num>
            <subsection eId="sec_3A__subsec_1">
              <num>(1)</num>
              <content>
                <p>Section 3A, subsection (1).</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <part eId="part_3">
        <num>3</num>
        <chapter eId="part_3__chp_1">
          <num>1</num>
          <section eId="sec_4">
            <content>
              <p>The fourth section.</p>
            </content>
          </section>
        </chapter>
      </part>
    </body>
  </act>
</akomaNtoso>""",
            output
        )

    def test_items(self):
        migration = AKNeId()
        items_input = """
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section id="section-100">
        <subsection id="section-100.3A.2">
          <blockList id="section-100.3A.2.list6">
            <item id="section-100.3A.2.list6.i">
              <p>item text</p>
            </item>
            <item id="section-100.3A.2.list6.ii.c">
              <p>item text</p>
            </item>
            <item id="section-100.3A.2.list6.iii">
              <blockList id="section-100.3A.2.list6.iii.list0">
                <item id="section-100.3A.2.list6.iii.list0.a">
                  <p>item text</p>
                </item>
                <item id="section-100.3A.2.list6.iii.list0.b.1.i">
                  <p>item text</p>
                </item>
              </blockList>
            </item>
          </blockList>
        </subsection>
      </section>
    </body>
  </act>
</akomaNtoso>"""
        items_output = migration.update_xml(items_input)
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section eId="sec_100">
        <subsection eId="sec_100__subsec_3A-2">
          <blockList eId="sec_100__subsec_3A-2__list_6">
            <item eId="sec_100__subsec_3A-2__list_6__item_i">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_6__item_ii-c">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_6__item_iii">
              <blockList eId="sec_100__subsec_3A-2__list_6__item_iii__list_0">
                <item eId="sec_100__subsec_3A-2__list_6__item_iii__list_0__item_a">
                  <p>item text</p>
                </item>
                <item eId="sec_100__subsec_3A-2__list_6__item_iii__list_0__item_b-1-i">
                  <p>item text</p>
                </item>
              </blockList>
            </item>
          </blockList>
        </subsection>
      </section>
    </body>
  </act>
</akomaNtoso>""",
            items_output
        )

