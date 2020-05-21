# coding=utf-8
from django.test import TestCase

from cobalt import Act

from indigo_api.data_migrations import AKNMigration, CrossheadingToHcontainer, UnnumberedParagraphsToHcontainer, ComponentSchedulesToAttachments, AKNeId, HrefMigration, AnnotationsMigration
from indigo_api.models import Document, Work


class MigrationTestCase(TestCase):
    maxDiff = None

    def setUp(self):
        self.work = Work(frbr_uri='/za/act/2019/1')

    def chain_mappings(self, mappings):
        pass

    def test_safe_update(self):
        migration = AKNMigration()
        element = "foo"
        mappings = {"ABC": "XYZ"}
        with self.assertRaises(AssertionError):
            migration.safe_update(element, mappings, "ABC", "DEF")

    def test_full_migration(self):
        """ Include tests for:
            - CrossheadingToHcontainer
            -
            -
            -
            -
        """
        mappings = {}
        cobalt_doc = Act("""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management"/>
          <FRBRalias value="Air Quality Management"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
          <FRBRdate date="2020-01-27" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="7662" name="Western Cape Provincial Gazette" showAs="Western Cape Provincial Gazette" date="2016-08-17"/>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
        <TLCTerm id="term-Air_Quality_Act" showAs="Air Quality Act" href="/ontology/term/this.eng.Air_Quality_Act"/>
        <TLCTerm id="term-adverse_effect" showAs="adverse effect" href="/ontology/term/this.eng.adverse_effect"/>
        <TLCTerm id="term-air_pollutant" showAs="air pollutant" href="/ontology/term/this.eng.air_pollutant"/>
        <TLCTerm id="term-air_pollution" showAs="air pollution" href="/ontology/term/this.eng.air_pollution"/>
        <TLCTerm id="term-air_pollution_control_zone" showAs="air pollution control zone" href="/ontology/term/this.eng.air_pollution_control_zone"/>
        <TLCTerm id="term-air_quality_management_plan" showAs="air quality management plan" href="/ontology/term/this.eng.air_quality_management_plan"/>
        <TLCTerm id="term-air_quality_officer" showAs="air quality officer" href="/ontology/term/this.eng.air_quality_officer"/>
        <TLCTerm id="term-ambient_air" showAs="ambient air" href="/ontology/term/this.eng.ambient_air"/>
        <TLCTerm id="term-atmosphere" showAs="atmosphere" href="/ontology/term/this.eng.atmosphere"/>
        <TLCTerm id="term-atmospheric_emission" showAs="atmospheric emission" href="/ontology/term/this.eng.atmospheric_emission"/>
        <TLCTerm id="term-authorised_official" showAs="authorised official" href="/ontology/term/this.eng.authorised_official"/>
        <TLCTerm id="term-best_practicable_environmental_option" showAs="best practicable environmental option" href="/ontology/term/this.eng.best_practicable_environmental_option"/>
        <TLCTerm id="term-burnt_metal" showAs="burnt metal" href="/ontology/term/this.eng.burnt_metal"/>
        <TLCTerm id="term-chimney" showAs="chimney" href="/ontology/term/this.eng.chimney"/>
        <TLCTerm id="term-City" showAs="City" href="/ontology/term/this.eng.City"/>
        <TLCTerm id="term-City_Manager" showAs="City Manager" href="/ontology/term/this.eng.City_Manager"/>
        <TLCTerm id="term-compression_ignition_powered_vehicle" showAs="compression ignition powered vehicle" href="/ontology/term/this.eng.compression_ignition_powered_vehicle"/>
        <TLCTerm id="term-continuing_offence" showAs="continuing offence" href="/ontology/term/this.eng.continuing_offence"/>
        <TLCTerm id="term-Council" showAs="Council" href="/ontology/term/this.eng.Council"/>
        <TLCTerm id="term-dark_smoke" showAs="dark smoke" href="/ontology/term/this.eng.dark_smoke"/>
        <TLCTerm id="term-directive" showAs="directive" href="/ontology/term/this.eng.directive"/>
        <TLCTerm id="term-dust" showAs="dust" href="/ontology/term/this.eng.dust"/>
        <TLCTerm id="term-dwelling" showAs="dwelling" href="/ontology/term/this.eng.dwelling"/>
        <TLCTerm id="term-environment" showAs="environment" href="/ontology/term/this.eng.environment"/>
        <TLCTerm id="term-Executive_Director__City_Health" showAs="Executive Director: City Health" href="/ontology/term/this.eng.Executive_Director__City_Health"/>
        <TLCTerm id="term-free_acceleration_test" showAs="free acceleration test" href="/ontology/term/this.eng.free_acceleration_test"/>
        <TLCTerm id="term-fuel_burning_equipment" showAs="fuel-burning equipment" href="/ontology/term/this.eng.fuel_burning_equipment"/>
        <TLCTerm id="term-light_absorption_meter" showAs="light absorption meter" href="/ontology/term/this.eng.light_absorption_meter"/>
        <TLCTerm id="term-living_organism" showAs="living organism" href="/ontology/term/this.eng.living_organism"/>
        <TLCTerm id="term-Municipal_Systems_Act" showAs="Municipal Systems Act" href="/ontology/term/this.eng.Municipal_Systems_Act"/>
        <TLCTerm id="term-nuisance" showAs="nuisance" href="/ontology/term/this.eng.nuisance"/>
        <TLCTerm id="term-obscuration" showAs="obscuration" href="/ontology/term/this.eng.obscuration"/>
        <TLCTerm id="term-open_burning" showAs="open burning" href="/ontology/term/this.eng.open_burning"/>
        <TLCTerm id="term-operator" showAs="operator" href="/ontology/term/this.eng.operator"/>
        <TLCTerm id="term-person" showAs="person" href="/ontology/term/this.eng.person"/>
        <TLCTerm id="term-premises" showAs="premises" href="/ontology/term/this.eng.premises"/>
        <TLCTerm id="term-Provincial_Government" showAs="Provincial Government" href="/ontology/term/this.eng.Provincial_Government"/>
        <TLCTerm id="term-public_road" showAs="public road" href="/ontology/term/this.eng.public_road"/>
        <TLCTerm id="term-smoke" showAs="smoke" href="/ontology/term/this.eng.smoke"/>
        <TLCTerm id="term-specialist_study" showAs="specialist study" href="/ontology/term/this.eng.specialist_study"/>
        <TLCTerm id="term-spray_area" showAs="spray area" href="/ontology/term/this.eng.spray_area"/>
        <TLCTerm id="term-unauthorised_burning" showAs="unauthorised burning" href="/ontology/term/this.eng.unauthorised_burning"/>
        <TLCTerm id="term-vehicle" showAs="vehicle" href="/ontology/term/this.eng.vehicle"/>
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
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <paragraph id="section-1.paragraph0">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Air_Quality_Act">"<def refersTo="#term-Air_Quality_Act">Air Quality Act</def>" means the National Environmental Management: Air Quality Act, 2004 (<ref href="/za/act/2004/39">Act No. 39 of 2004</ref>);</p>
              <p refersTo="#term-adverse_effect">"<def refersTo="#term-adverse_effect">adverse effect</def>" means any actual or potential impact on the <term refersTo="#term-environment" id="trm0">environment</term> that impairs or would impair the <term refersTo="#term-environment" id="trm1">environment</term> or any aspect of it to an extent that is more than trivial or insignificant;</p>
              <p refersTo="#term-air_pollutant">"<def refersTo="#term-air_pollutant">air pollutant</def>" includes any <term refersTo="#term-dust" id="trm2">dust</term>, <term refersTo="#term-smoke" id="trm3">smoke</term>, fumes or gas that causes or may cause <term refersTo="#term-air_pollution" id="trm4">air pollution</term>;</p>
              <p refersTo="#term-air_pollution">"<def refersTo="#term-air_pollution">air pollution</def>" means any change in the <term refersTo="#term-environment" id="trm5">environment</term> caused by any substance emitted into the <term refersTo="#term-atmosphere" id="trm6">atmosphere</term> from any activity, where that change has an <term refersTo="#term-adverse_effect" id="trm7">adverse effect</term> on human health or well-being or on the composition, resilience and productivity of natural or managed ecosystems, or on materials useful to people, or will have such an effect in the future;</p>
              <p refersTo="#term-air_pollution_control_zone">"<def refersTo="#term-air_pollution_control_zone">air pollution control zone</def>" means a geographical area declared in terms of section 8 of the By-Law to be an air pollution control zone for purposes of Chapter IV of the By-Law;</p>
              <p refersTo="#term-air_quality_management_plan">"<def refersTo="#term-air_quality_management_plan">air quality management plan</def>" means the air quality management plan referred to in section 15 of the <term refersTo="#term-Air_Quality_Act" id="trm8">Air Quality Act</term>;</p>
              <p refersTo="#term-air_quality_officer">"<def refersTo="#term-air_quality_officer">air quality officer</def>" means the air quality officer designated as such in terms of section 14(3) of the <term refersTo="#term-Air_Quality_Act" id="trm9">Air Quality Act</term>;</p>
              <p refersTo="#term-ambient_air">"<def refersTo="#term-ambient_air">ambient air</def>" means "ambient air" as defined in section 1 of the <term refersTo="#term-Air_Quality_Act" id="trm10">Air Quality Act</term>;</p>
              <p refersTo="#term-atmosphere">"<def refersTo="#term-atmosphere">atmosphere</def>" means air that is not enclosed by a building, machine, <term refersTo="#term-chimney" id="trm11">chimney</term> or other similar structure;</p>
              <p refersTo="#term-atmospheric_emission">"<def refersTo="#term-atmospheric_emission">atmospheric emission</def>" or "emission" means any emission or entrainment process emanating from a point, non-point or mobile source, as defined in the <term refersTo="#term-Air_Quality_Act" id="trm12">Air Quality Act</term> that results in <term refersTo="#term-air_pollution" id="trm13">air pollution</term>;</p>
              <p refersTo="#term-authorised_official">"<def refersTo="#term-authorised_official">authorised official</def>" means an employee of the <term refersTo="#term-City" id="trm14">City</term> responsible for carrying out any duty or function or exercising any power in terms of this By-law, and includes employees delegated to carry out or exercise such duties, functions or powers;</p>
              <p refersTo="#term-best_practicable_environmental_option">"<def refersTo="#term-best_practicable_environmental_option">best practicable environmental option</def>" means the option that provides the most benefit, or causes the least damage to the <term refersTo="#term-environment" id="trm15">environment</term> as a whole, at a cost acceptable in the long term as well as in the short term;</p>
              <p refersTo="#term-burnt_metal">"<def refersTo="#term-burnt_metal">burnt metal</def>" means any metal that has had its exterior coating removed by means of burning in any place or device other than an approved incineration device, for the purpose of recovering the metal beneath the exterior coating;</p>
              <p refersTo="#term-chimney">"<def refersTo="#term-chimney">chimney</def>" means any structure or opening of any kind from which or through which air pollutants may be emitted;</p>
              <p refersTo="#term-City">"<def refersTo="#term-City">City</def>" means the City of Cape Town established by Provincial Notice No. 479 of 2000 in terms of section 12 of the Local Government: Municipal Structures Act, 1998 (<ref href="/za/act/1998/117">Act No. 117 of 1998</ref>) or any structure or employee of the City acting in terms of delegated authority;</p>
              <p refersTo="#term-City_Manager">"<def refersTo="#term-City_Manager">City Manager</def>" means a <term refersTo="#term-person" id="trm16">person</term> appointed by the <term refersTo="#term-Council" id="trm17">Council</term> in terms of section 54A of the Local Government: <term refersTo="#term-Municipal_Systems_Act" id="trm18">Municipal Systems Act</term>, 2000 (<ref href="/za/act/2000/32">Act No. 32 of 2000</ref>);</p>
              <p refersTo="#term-compression_ignition_powered_vehicle">"<def refersTo="#term-compression_ignition_powered_vehicle">compression ignition powered vehicle</def>" means a <term refersTo="#term-vehicle" id="trm19">vehicle</term> powered by an internal combustion, compression ignition, diesel or similar fuel engine;</p>
              <p refersTo="#term-continuing_offence">"<def refersTo="#term-continuing_offence">continuing offence</def>" means an offence where the act or omission giving rise to the issuing of a notice has not been repaired, removed or rectified by the expiry of a notice issued in terms of this By-law;</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.paragraph0.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.paragraph0.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <p refersTo="#term-directive">"<def refersTo="#term-directive">directive</def>" means an instruction issued by the delegated authority for a <term refersTo="#term-person" id="trm29">person</term> to perform or cease to perform certain activities in order to prevent any detrimental effect on air quality, health or the <term refersTo="#term-environment" id="trm30">environment</term>;</p>
              <p refersTo="#term-dust">"<def refersTo="#term-dust">dust</def>" means any solid matter in a fine or disintegrated form which is capable of being dispersed or suspended in the <term refersTo="#term-atmosphere" id="trm31">atmosphere</term>;</p>
              <p refersTo="#term-dwelling">"<def refersTo="#term-dwelling">dwelling</def>" means any building or structure, or part of a building or structure used as a place of temporary or permanent residence, and includes any outbuilding or other structure ancillary to it;</p>
              <blockList id="section-1.paragraph0.list1" refersTo="#term-environment">
                <listIntroduction>"<def refersTo="#term-environment">environment</def>" means the surroundings within which humans exist and that are made up of-</listIntroduction>
                <item id="section-1.paragraph0.list1.a">
                  <num>(a)</num>
                  <p>the land, water and <term refersTo="#term-atmosphere" id="trm32">atmosphere</term> of the earth;</p>
                </item>
                <item id="section-1.paragraph0.list1.b">
                  <num>(b)</num>
                  <p>micro-organisms, plant and animal life;</p>
                </item>
                <item id="section-1.paragraph0.list1.c">
                  <num>(c)</num>
                  <p>any part or combination of (a) and (b) and the interrelationships among and between them; and</p>
                </item>
                <item id="section-1.paragraph0.list1.d">
                  <num>(d)</num>
                  <p>the physical, chemical, aesthetic and cultural properties and conditions of the foregoing that influence human health and well-being;</p>
                </item>
              </blockList>
              <p refersTo="#term-Executive_Director__City_Health">"<def refersTo="#term-Executive_Director__City_Health">Executive Director: City Health</def>" means the Executive Director of the <term refersTo="#term-City" id="trm33">City</term> responsible for health matters;</p>
              <p refersTo="#term-free_acceleration_test">"<def refersTo="#term-free_acceleration_test">free acceleration test</def>" means the testing procedure described in <ref href="#section-23">section 23</ref>;</p>
              <blockList id="section-1.paragraph0.list2" refersTo="#term-fuel_burning_equipment">
                <listIntroduction>"<def refersTo="#term-fuel_burning_equipment">fuel-burning equipment</def>" means any installed furnace, boiler, burner, incinerator, smoking device, wood-fired oven, commercial wood or charcoal fired braai, barbecue or other equipment including a <term refersTo="#term-chimney" id="trm34">chimney</term>–</listIntroduction>
                <item id="section-1.paragraph0.list2.a">
                  <num>(a)</num>
                  <p>designed to burn or capable of burning liquid, gas or solid fuel;</p>
                </item>
                <item id="section-1.paragraph0.list2.b">
                  <num>(b)</num>
                  <p>used to dispose of any material including general and hazardous waste by the application of heat at a rate of less than 10 kg of waste per day; or</p>
                </item>
                <item id="section-1.paragraph0.list2.c">
                  <num>(c)</num>
                  <p>used to subject liquid, gas or solid fuel to any process involving the application of heat;</p>
                </item>
              </blockList>
              <p>but excludes standby generators and temporary standby generators; domestic <term refersTo="#term-fuel_burning_equipment" id="trm35">fuel-burning equipment</term>; and gas-fired commercial cooking equipment;</p>
              <p refersTo="#term-light_absorption_meter">"<def refersTo="#term-light_absorption_meter">light absorption meter</def>" means a measuring device that uses a light sensitive cell or detector to determine the amount of light absorbed by an <term refersTo="#term-air_pollutant" id="trm36">air pollutant</term>;</p>
              <p refersTo="#term-living_organism">"<def refersTo="#term-living_organism">living organism</def>" means any biological entity capable of transferring or replicating genetic material, including sterile organisms and viruses;</p>
              <p refersTo="#term-Municipal_Systems_Act">"<def refersTo="#term-Municipal_Systems_Act">Municipal Systems Act</def>" means the Local Government: Municipal Systems Act, 2000, (Act No. 32 of);</p>
              <blockList id="section-1.paragraph0.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.paragraph0.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.paragraph0.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
              <p refersTo="#term-obscuration">"<def refersTo="#term-obscuration">obscuration</def>" means the ratio of visible light attenuated by air pollutants suspended in the effluent streams to incident visible light, expressed as a percentage;</p>
              <p refersTo="#term-open_burning">"<def refersTo="#term-open_burning">open burning</def>" means the combustion of any material by burning without a <term refersTo="#term-chimney" id="trm41">chimney</term> to vent the emitted products of combustion to the <term refersTo="#term-atmosphere" id="trm42">atmosphere</term> and includes fires for fire safety training purposes, but excludes any recreational or commercial braai, and "burning in the open" has a corresponding meaning;</p>
              <p refersTo="#term-operator">"<def refersTo="#term-operator">operator</def>" means a <term refersTo="#term-person" id="trm43">person</term> who owns or manages an undertaking, or who controls an operation or process, which emits air pollutants;</p>
              <p refersTo="#term-person">"<def refersTo="#term-person">person</def>" means a natural person or a juristic person;</p>
              <blockList id="section-1.paragraph0.list4" refersTo="#term-premises">
                <listIntroduction>"<def refersTo="#term-premises">premises</def>" includes-</listIntroduction>
                <item id="section-1.paragraph0.list4.a">
                  <num>(a)</num>
                  <p>any building or other structure;</p>
                </item>
                <item id="section-1.paragraph0.list4.b">
                  <num>(b)</num>
                  <p>any adjoining land occupied or used in connection with any activities carried on in that building or structure;</p>
                </item>
                <item id="section-1.paragraph0.list4.c">
                  <num>(c)</num>
                  <p>any vacant land;</p>
                </item>
                <item id="section-1.paragraph0.list4.d">
                  <num>(d)</num>
                  <p>any locomotive, ship, boat or other vessel which operates in the jurisdiction of the <term refersTo="#term-City" id="trm44">City</term> of Cape Town; and</p>
                </item>
                <item id="section-1.paragraph0.list4.e">
                  <num>(e)</num>
                  <p>any State-owned entity or land;</p>
                </item>
              </blockList>
              <p refersTo="#term-Provincial_Government">"<def refersTo="#term-Provincial_Government">Provincial Government</def>" means the Provincial Government of the Western Cape;</p>
              <p refersTo="#term-public_road">"<def refersTo="#term-public_road">public road</def>" means a road which the public has the right to use;</p>
              <p refersTo="#term-smoke">"<def refersTo="#term-smoke">smoke</def>" means the gases, particulate matter and products of combustion emitted into the <term refersTo="#term-atmosphere" id="trm45">atmosphere</term> when material is burned or subjected to heat and includes the soot, grit and gritty particles emitted in smoke;</p>
              <p refersTo="#term-specialist_study">"<def refersTo="#term-specialist_study">specialist study</def>" means any scientifically based study relating to air quality conducted by an expert or recognised specialist of appropriate qualifications and competency in the discipline of air quality management;</p>
              <p refersTo="#term-spray_area">"<def refersTo="#term-spray_area">spray area</def>" means an area or enclosure referred to in <ref href="#section-25">section 25</ref> used for spray painting, and "spray booth" has a corresponding meaning;</p>
              <p refersTo="#term-unauthorised_burning">"<def refersTo="#term-unauthorised_burning">unauthorised burning</def>" means burning of any material in any place or device on any <term refersTo="#term-premises" id="trm46">premises</term> other than in an approved incineration device without obtaining the prior written authorisation of the <term refersTo="#term-City" id="trm47">City</term>; and</p>
              <p refersTo="#term-vehicle">"<def refersTo="#term-vehicle">vehicle</def>" means any motor car, motor cycle, bus, motor lorry or other conveyance propelled wholly or partly by any volatile spirit, steam, gas or oil, or by any means other than human or animal power.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <paragraph id="section-2.paragraph0">
            <content>
              <p>This By-law applies to all properties or <term refersTo="#term-premises" id="trm48">premises</term> within the area of jurisdiction of the <term refersTo="#term-City" id="trm49">City</term> of Cape Town.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-3">
          <num>3.</num>
          <heading>Conflict with other laws</heading>
          <paragraph id="section-3.paragraph0">
            <content>
              <p>In the event of any conflict between this By-law and any other by-law or any policy which regulates <term refersTo="#term-air_pollution" id="trm50">air pollution</term>, the provisions of this By-law shall prevail in so far as it relates to air quality management.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-II">
        <num>II</num>
        <heading>Duty of care</heading>
        <section id="section-4">
          <num>4.</num>
          <heading>Reasonable measures to prevent <term refersTo="#term-air_pollution" id="trm51">air pollution</term></heading>
          <subsection id="section-4.1">
            <num>(1)</num>
            <content>
              <blockList id="section-4.1.list0">
                <listIntroduction>Any <term refersTo="#term-person" id="trm52">person</term> who is wholly or partially responsible for causing <term refersTo="#term-air_pollution" id="trm53">air pollution</term> or creating a risk of <term refersTo="#term-air_pollution" id="trm54">air pollution</term> occurring must take all reasonable measures including the <term refersTo="#term-best_practicable_environmental_option" id="trm55">best practicable environmental option</term>–</listIntroduction>
                <item id="section-4.1.list0.a">
                  <num>(a)</num>
                  <p>to prevent any potential significant <term refersTo="#term-air_pollution" id="trm56">air pollution</term> from occurring; and</p>
                </item>
                <item id="section-4.1.list0.b">
                  <num>(b)</num>
                  <p>to mitigate and, as far as reasonably possible, remedy the environmental impacts and consequences of any <term refersTo="#term-air_pollution" id="trm57">air pollution</term> that has occurred.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-4.2">
            <num>(2)</num>
            <content>
              <blockList id="section-4.2.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm58">City</term> may direct any <term refersTo="#term-person" id="trm59">person</term> who fails to take the measures required under subsection (1) to—</listIntroduction>
                <item id="section-4.2.list0.a">
                  <num>(a)</num>
                  <p>investigate, evaluate and assess the impact on the <term refersTo="#term-environment" id="trm60">environment</term> of specific activities and report thereon;</p>
                </item>
                <item id="section-4.2.list0.b">
                  <num>(b)</num>
                  <p>take specific reasonable measures before a given date;</p>
                </item>
                <item id="section-4.2.list0.c">
                  <num>(c)</num>
                  <p>diligently continue with those measures; and</p>
                </item>
                <item id="section-4.2.list0.d">
                  <num>(d)</num>
                  <p>complete them before a specified reasonable date,</p>
                </item>
              </blockList>
              <p>provided that prior to such direction the <term refersTo="#term-City" id="trm61">City</term> must give such <term refersTo="#term-person" id="trm62">person</term> adequate notice and direct him or her to inform the authorised official of his or her relevant interests.</p>
            </content>
          </subsection>
          <subsection id="section-4.3">
            <num>(3)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm63">City</term> may, if a <term refersTo="#term-person" id="trm64">person</term> fails to comply or inadequately complies with a <term refersTo="#term-directive" id="trm65">directive</term> contemplated in subsection (2), take reasonable measures to remedy the situation.</p>
            </content>
          </subsection>
          <subsection id="section-4.4">
            <num>(4)</num>
            <content>
              <blockList id="section-4.4.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm66">City</term> may, if a <term refersTo="#term-person" id="trm67">person</term> fails to carry out the measures referred to in subsection (1), recover all reasonable costs incurred as a result of it acting under subsection (3) from any or all of the following persons:</listIntroduction>
                <item id="section-4.4.list0.a">
                  <num>(a)</num>
                  <p>any <term refersTo="#term-person" id="trm68">person</term> who is or was responsible for, or who directly or indirectly contributed to the <term refersTo="#term-air_pollution" id="trm69">air pollution</term> or the potential <term refersTo="#term-air_pollution" id="trm70">air pollution</term>;</p>
                </item>
                <item id="section-4.4.list0.b">
                  <num>(b)</num>
                  <p>the owner of the land at the time when the <term refersTo="#term-air_pollution" id="trm71">air pollution</term> or the potential for <term refersTo="#term-air_pollution" id="trm72">air pollution</term> occurred;</p>
                </item>
                <item id="section-4.4.list0.c">
                  <num>(c)</num>
                  <blockList id="section-4.4.list0.c.list0">
                    <listIntroduction>the <term refersTo="#term-person" id="trm73">person</term> in control of the land or any <term refersTo="#term-person" id="trm74">person</term> who has or had a right to use the land at the time when the—</listIntroduction>
                    <item id="section-4.4.list0.c.list0.i">
                      <num>(i)</num>
                      <p>activity or the process in question is or was performed or undertaken; or</p>
                    </item>
                    <item id="section-4.4.list0.c.list0.ii">
                      <num>(ii)</num>
                      <p>situation came about; or</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-4.4.list0.d">
                  <num>(d)</num>
                  <blockList id="section-4.4.list0.d.list0">
                    <listIntroduction>any <term refersTo="#term-person" id="trm75">person</term> who negligently failed to prevent the—</listIntroduction>
                    <item id="section-4.4.list0.d.list0.i">
                      <num>(i)</num>
                      <p>activity or the process being performed or undertaken; or</p>
                    </item>
                    <item id="section-4.4.list0.d.list0.ii">
                      <num>(ii)</num>
                      <p>situation from coming about.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-4.5">
            <num>(5)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm76">person</term> who fails to comply with a <term refersTo="#term-directive" id="trm77">directive</term> referred to in 4(2) commits an offence in terms of Chapter XI of this By-Law.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-III">
        <num>III</num>
        <heading>Designation of the <term refersTo="#term-air_quality_officer" id="trm78">air quality officer</term></heading>
        <section id="section-5">
          <num>5.</num>
          <heading>Designation or appointment of the <term refersTo="#term-air_quality_officer" id="trm79">air quality officer</term></heading>
          <paragraph id="section-5.paragraph0">
            <content>
              <p>The <term refersTo="#term-City_Manager" id="trm80">City Manager</term> must, in consultation with the <term refersTo="#term-Executive_Director__City_Health" id="trm81">Executive Director: City Health</term>, designate or appoint an employee of the <term refersTo="#term-City" id="trm82">City</term> as the Air Quality Officer to be responsible for co-ordinating matters pertaining to air quality management and granting or rejecting Atmospheric Emission Licences or Provisional Atmospheric Emission Licences in terms of the <term refersTo="#term-Air_Quality_Act" id="trm83">Air Quality Act</term> within the <term refersTo="#term-City" id="trm84">City</term>’s jurisdiction.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-IV">
        <num>IV</num>
        <heading>Local emissions standards, norms and standards and <term refersTo="#term-smoke" id="trm85">smoke</term> control zones</heading>
        <part id="chapter-IV.part-1">
          <num>1</num>
          <heading>Local emissions standards</heading>
          <section id="section-6">
            <num>6.</num>
            <heading>Legal mandate</heading>
            <subsection id="section-6.1">
              <num>(1)</num>
              <content>
                <blockList id="section-6.1.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm86">City</term> may, by notice -</listIntroduction>
                  <item id="section-6.1.list0.a">
                    <num>(a)</num>
                    <p>identify substances or mixtures of substances in <term refersTo="#term-ambient_air" id="trm87">ambient air</term> which, through ambient concentrations, bioaccumulation, deposition or in any other way, present a threat to health, well-being or the <term refersTo="#term-environment" id="trm88">environment</term> in the area of jurisdiction of the <term refersTo="#term-City" id="trm89">City</term> of Cape Town or which the <term refersTo="#term-air_quality_officer" id="trm90">air quality officer</term> reasonably believes present such a threat; and</p>
                  </item>
                  <item id="section-6.1.list0.b">
                    <num>(b)</num>
                    <p>in respect of each of those substances or mixtures of substances, publish local standards for emissions from point, non-point or mobile sources in the area of jurisdiction of <term refersTo="#term-City" id="trm91">City</term> of Cape Town.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-6.2">
              <num>(2)</num>
              <content>
                <blockList id="section-6.2.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm92">City</term> may take the following factors into consideration in setting local emission standards:</listIntroduction>
                  <item id="section-6.2.list0.a">
                    <num>(a)</num>
                    <p>health, safety and environmental protection objectives;</p>
                  </item>
                  <item id="section-6.2.list0.b">
                    <num>(b)</num>
                    <p>analytical methodology;</p>
                  </item>
                  <item id="section-6.2.list0.c">
                    <num>(c)</num>
                    <p>technical feasibility;</p>
                  </item>
                  <item id="section-6.2.list0.d">
                    <num>(d)</num>
                    <p>monitoring capability;</p>
                  </item>
                  <item id="section-6.2.list0.e">
                    <num>(e)</num>
                    <p>socio-economic consequences;</p>
                  </item>
                  <item id="section-6.2.list0.f">
                    <num>(f)</num>
                    <p>ecological role of fire in vegetation remnants; and</p>
                  </item>
                  <item id="section-6.2.list0.g">
                    <num>(g)</num>
                    <p><term refersTo="#term-best_practicable_environmental_option" id="trm93">best practicable environmental option</term>.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-6.3">
              <num>(3)</num>
              <content>
                <p>Any <term refersTo="#term-person" id="trm94">person</term> who is emitting substances or mixtures of substances as referred to in subsection (1) must comply with the local emission standards published in terms of this By-law and the failure to do so constitutes an offence in terms of Chapter XI of this By-law.</p>
              </content>
            </subsection>
          </section>
        </part>
        <part id="chapter-IV.part-2">
          <num>2</num>
          <heading>Norms and standards</heading>
          <section id="section-7">
            <num>7.</num>
            <heading>Substances identification process</heading>
            <subsection id="section-7.1">
              <num>(1)</num>
              <content>
                <blockList id="section-7.1.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm95">City</term> must when identifying and prioritising the substances in <term refersTo="#term-ambient_air" id="trm96">ambient air</term> that present a threat to public health, well-being or the <term refersTo="#term-environment" id="trm97">environment</term> consider the following:</listIntroduction>
                  <item id="section-7.1.list0.a">
                    <num>(a)</num>
                    <p>the possibility, severity and frequency of effects with regard to human health and the <term refersTo="#term-environment" id="trm98">environment</term> as a whole, with irreversible effects being of special concern;</p>
                  </item>
                  <item id="section-7.1.list0.b">
                    <num>(b)</num>
                    <p>ubiquitous and high concentrations of the substance in the <term refersTo="#term-atmosphere" id="trm99">atmosphere</term>;</p>
                  </item>
                  <item id="section-7.1.list0.c">
                    <num>(c)</num>
                    <p>potential environmental transformations and metabolic alterations of the substance, as these changes may lead to the production of chemicals with greater toxicity persistence in the <term refersTo="#term-environment" id="trm100">environment</term>, particularly if the substance is not biodegradable and is able to accumulate in humans, the <term refersTo="#term-environment" id="trm101">environment</term> or food chains;</p>
                  </item>
                  <item id="section-7.1.list0.d">
                    <num>(d)</num>
                    <blockList id="section-7.1.list0.d.list0">
                      <listIntroduction>the impact of the substance taking the following factors into consideration:</listIntroduction>
                      <item id="section-7.1.list0.d.list0.i">
                        <num>(i)</num>
                        <p>size of the exposed population, living resources or ecosystems;</p>
                      </item>
                      <item id="section-7.1.list0.d.list0.ii">
                        <num>(ii)</num>
                        <p>the existence of particularly sensitive receptors in the zone concerned; and</p>
                      </item>
                    </blockList>
                  </item>
                  <item id="section-7.1.list0.e">
                    <num>(e)</num>
                    <p>substances that are regulated by international conventions.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-7.2">
              <num>(2)</num>
              <content>
                <p>The <term refersTo="#term-air_quality_officer" id="trm102">air quality officer</term> must, using the criteria set out in subsection (1), compile a list of substances in <term refersTo="#term-ambient_air" id="trm103">ambient air</term> that present a threat to public health, well-being or the <term refersTo="#term-environment" id="trm104">environment</term>.</p>
              </content>
            </subsection>
          </section>
          <section id="section-8">
            <num>8.</num>
            <heading>Declaration of <term refersTo="#term-air_pollution_control_zone" id="trm105">air pollution control zone</term></heading>
            <subsection id="section-8.1">
              <num>(1)</num>
              <content>
                <p>The entire area of the jurisdiction of the <term refersTo="#term-City" id="trm106">City</term> of Cape Town is hereby declared to be an <term refersTo="#term-air_pollution_control_zone" id="trm107">air pollution control zone</term>.</p>
              </content>
            </subsection>
            <subsection id="section-8.2">
              <num>(2)</num>
              <content>
                <blockList id="section-8.2.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm108">City</term> may, within the <term refersTo="#term-air_pollution_control_zone" id="trm109">air pollution control zone</term>, from time to time by notice in the Provincial Gazette -</listIntroduction>
                  <item id="section-8.2.list0.a">
                    <num>(a)</num>
                    <p>prohibit or restrict the emission of one or more air pollutants from all <term refersTo="#term-premises" id="trm110">premises</term> or certain <term refersTo="#term-premises" id="trm111">premises</term>;</p>
                  </item>
                  <item id="section-8.2.list0.b">
                    <num>(b)</num>
                    <p>prohibit or restrict the combustion of certain types of fuel;</p>
                  </item>
                  <item id="section-8.2.list0.c">
                    <num>(c)</num>
                    <blockList id="section-8.2.list0.c.list0">
                      <listIntroduction>prescribe different requirements in an <term refersTo="#term-air_pollution_control_zone" id="trm112">air pollution control zone</term> relating to air quality in respect of:</listIntroduction>
                      <item id="section-8.2.list0.c.list0.i">
                        <num>(i)</num>
                        <p>different geographical portions;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.ii">
                        <num>(ii)</num>
                        <p>specified <term refersTo="#term-premises" id="trm113">premises</term>;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.iii">
                        <num>(iii)</num>
                        <p>classes of <term refersTo="#term-premises" id="trm114">premises</term>;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.iv">
                        <num>(iv)</num>
                        <p><term refersTo="#term-premises" id="trm115">premises</term> used for specified purposes; or</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.v">
                        <num>(v)</num>
                        <p>mobile sources.</p>
                      </item>
                    </blockList>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-8.3">
              <num>(3)</num>
              <content>
                <p>The <term refersTo="#term-City" id="trm116">City</term> may develop and publish policies and guidelines, including technical guidelines, nrelating to the regulation of activities which directly and indirectly cause <term refersTo="#term-air_pollution" id="trm117">air pollution</term> within an <term refersTo="#term-air_pollution_control_zone" id="trm118">air pollution control zone</term>.</p>
              </content>
            </subsection>
            <subsection id="section-8.4">
              <num>(4)</num>
              <content>
                <p>No owner or occupier of any <term refersTo="#term-premises" id="trm119">premises</term> shall cause or permit the emanation or emission of <term refersTo="#term-smoke" id="trm120">smoke</term> of such a density or content from such <term refersTo="#term-premises" id="trm121">premises</term> as will obscure light to an extent greater than twenty (20) per cent.</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <chapter id="chapter-V">
        <num>V</num>
        <heading>Smoke emissions from <term refersTo="#term-premises" id="trm122">premises</term> other than dwellings</heading>
        <section id="section-9">
          <num>9.</num>
          <heading>Application</heading>
          <paragraph id="section-9.paragraph0">
            <content>
              <p>For the purposes of this Chapter "<term refersTo="#term-premises" id="trm123">premises</term>" does not include dwellings.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-10">
          <num>10.</num>
          <heading>Prohibition of <term refersTo="#term-dark_smoke" id="trm124">dark smoke</term> from <term refersTo="#term-premises" id="trm125">premises</term></heading>
          <subsection id="section-10.1">
            <num>(1)</num>
            <content>
              <p>Subject to subsection (2), <term refersTo="#term-dark_smoke" id="trm126">dark smoke</term> must not be emitted from any <term refersTo="#term-premises" id="trm127">premises</term> for an aggregate period exceeding three (3) minutes during any continuous period of thirty (30) minutes.</p>
            </content>
          </subsection>
          <subsection id="section-10.2">
            <num>(2)</num>
            <content>
              <p>This section does not apply to <term refersTo="#term-dark_smoke" id="trm128">dark smoke</term> which is emitted from <term refersTo="#term-fuel_burning_equipment" id="trm129">fuel-burning equipment</term> while such equipment is being started, overhauled or repaired, unless such emission could have been prevented using the best practical environmental option.</p>
            </content>
          </subsection>
          <subsection id="section-10.3">
            <num>(3)</num>
            <content>
              <p>Subsections (1) and (2) do not apply to holders of <term refersTo="#term-atmospheric_emission" id="trm130">atmospheric emission</term> licences for activities listed in terms of section 21 of the <term refersTo="#term-Air_Quality_Act" id="trm131">Air Quality Act</term>, and the emission standards listed in such <term refersTo="#term-atmospheric_emission" id="trm132">atmospheric emission</term> licences shall apply.</p>
            </content>
          </subsection>
        </section>
        <section id="section-11">
          <num>11.</num>
          <heading>Installation of <term refersTo="#term-fuel_burning_equipment" id="trm133">fuel-burning equipment</term></heading>
          <subsection id="section-11.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm134">person</term> shall install, alter, extend, replace or operate any <term refersTo="#term-fuel_burning_equipment" id="trm135">fuel-burning equipment</term> on any <term refersTo="#term-premises" id="trm136">premises</term> without the prior written authorisation of the <term refersTo="#term-City" id="trm137">City</term>, which may only be given after consideration of the completed prescribed application form together with the relevant plans and specifications.</p>
            </content>
          </subsection>
          <subsection id="section-11.2">
            <num>(2)</num>
            <content>
              <p>No rights accrue to any <term refersTo="#term-person" id="trm138">person</term> who has applied for written authorisation in terms of subsection (1) during the interim period whilst the application is under consideration.</p>
            </content>
          </subsection>
          <subsection id="section-11.3">
            <num>(3)</num>
            <content>
              <p>A written authorisation granted by the <term refersTo="#term-City" id="trm139">City</term> in respect of the installation, alteration, extension, replacement or operation of any <term refersTo="#term-fuel_burning_equipment" id="trm140">fuel-burning equipment</term> in terms of a by-law concerned with air quality management or a regulation in terms of the Atmospheric Pollution Prevention Act, which has been repealed shall be deemed to satisfy the requirements of subsection (1) where proof of such authorisation is presented to the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-11.4">
            <num>(4)</num>
            <content>
              <blockList id="section-11.4.list0">
                <listIntroduction>Where <term refersTo="#term-fuel_burning_equipment" id="trm141">fuel-burning equipment</term> has been installed, altered, extended or replaced on <term refersTo="#term-premises" id="trm142">premises</term> contrary to subsection (1), the authorised official may, on written notice to the owner of the <term refersTo="#term-premises" id="trm143">premises</term> or to the <term refersTo="#term-operator" id="trm144">operator</term> of the appliance:</listIntroduction>
                <item id="section-11.4.list0.a">
                  <num>(a)</num>
                  <p>order the removal of the <term refersTo="#term-fuel_burning_equipment" id="trm145">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm146">premises</term>, at the expense of the owner, <term refersTo="#term-operator" id="trm147">operator</term> or both within the period stated in the notice, or,</p>
                </item>
                <item id="section-11.4.list0.b">
                  <num>(b)</num>
                  <p>impose a fine not exceeding R10 000 before considering an application for written authorisation in terms of subsection (1).</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-11.5">
            <num>(5)</num>
            <content>
              <p>When ownership of <term refersTo="#term-fuel_burning_equipment" id="trm148">fuel-burning equipment</term> which has been approved by the <term refersTo="#term-City" id="trm149">City</term> is transferred to a new owner, the new owner must apply for written authorisation to use such equipment in terms of subsection (1).</p>
            </content>
          </subsection>
          <subsection id="section-11.6">
            <num>(6)</num>
            <content>
              <p>Fuel-burning equipment must comply with the emission standards as contained in Schedule 1 of this By-law.</p>
            </content>
          </subsection>
        </section>
        <section id="section-12">
          <num>12.</num>
          <heading>Operation of <term refersTo="#term-fuel_burning_equipment" id="trm150">fuel-burning equipment</term></heading>
          <subsection id="section-12.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm151">person</term> may use or operate any <term refersTo="#term-fuel_burning_equipment" id="trm152">fuel-burning equipment</term> on any <term refersTo="#term-premises" id="trm153">premises</term> contrary to a written authorisation referred to in <ref href="#section-11">section 11</ref>(1).</p>
            </content>
          </subsection>
          <subsection id="section-12.2">
            <num>(2)</num>
            <content>
              <blockList id="section-12.2.list0">
                <listIntroduction>Where <term refersTo="#term-fuel_burning_equipment" id="trm154">fuel-burning equipment</term> has been used or operated on a <term refersTo="#term-premises" id="trm155">premises</term> contrary to subsection (1), the authorised official may on written notice to the owner of the <term refersTo="#term-premises" id="trm156">premises</term> or <term refersTo="#term-operator" id="trm157">operator</term> of the <term refersTo="#term-fuel_burning_equipment" id="trm158">fuel-burning equipment</term> -</listIntroduction>
                <item id="section-12.2.list0.a">
                  <num>(a)</num>
                  <p>revoke the written authorisation referred to in subsection (1); and</p>
                </item>
                <item id="section-12.2.list0.b">
                  <num>(b)</num>
                  <p>order the removal of the <term refersTo="#term-fuel_burning_equipment" id="trm159">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm160">premises</term> at the expense of the owner and <term refersTo="#term-operator" id="trm161">operator</term> within the period stated in the notice.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-12.3">
            <num>(3)</num>
            <content>
              <p>In the event that the owner of the <term refersTo="#term-premises" id="trm162">premises</term> or <term refersTo="#term-operator" id="trm163">operator</term> of the <term refersTo="#term-fuel_burning_equipment" id="trm164">fuel-burning equipment</term> fails to comply with a notice issued in terms of subsection (2), the authorised official may remove the <term refersTo="#term-fuel_burning_equipment" id="trm165">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm166">premises</term>, and recover the reasonable costs incurred from the owner or <term refersTo="#term-operator" id="trm167">operator</term> in question.</p>
            </content>
          </subsection>
        </section>
        <section id="section-13">
          <num>13.</num>
          <heading>Periodic Emissions Testing</heading>
          <paragraph id="section-13.paragraph0">
            <content>
              <p>The <term refersTo="#term-authorised_official" id="trm168">authorised official</term> may order the owner of the <term refersTo="#term-premises" id="trm169">premises</term> or <term refersTo="#term-operator" id="trm170">operator</term> of any <term refersTo="#term-fuel_burning_equipment" id="trm171">fuel-burning equipment</term> capable of burning solid fuels to conduct periodic emissions testing in accordance with the methods prescribed in Schedule 1 of this By-law.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-14">
          <num>14.</num>
          <heading>Presumption</heading>
          <subsection id="section-14.1">
            <num>(1)</num>
            <content>
              <p>Dark <term refersTo="#term-smoke" id="trm172">smoke</term> shall be presumed to have been emitted from a <term refersTo="#term-premises" id="trm173">premises</term> if it is shown that any fuel or material was burned on the <term refersTo="#term-premises" id="trm174">premises</term>, and that the circumstances were such that the burning was reasonably likely to give rise to the emission of <term refersTo="#term-dark_smoke" id="trm175">dark smoke</term>, unless the owner, occupier or <term refersTo="#term-operator" id="trm176">operator</term>, as the case may be, can show that no <term refersTo="#term-dark_smoke" id="trm177">dark smoke</term> was emitted.</p>
            </content>
          </subsection>
          <subsection id="section-14.2">
            <num>(2)</num>
            <content>
              <p>Where an <term refersTo="#term-authorised_official" id="trm178">authorised official</term> has observed <term refersTo="#term-fuel_burning_equipment" id="trm179">fuel-burning equipment</term> emitting particulate emissions; or <term refersTo="#term-dark_smoke" id="trm180">dark smoke</term> for a period of greater than 3 minutes in every aggregate half hour, the authorised official may issue a compliance notice ordering the <term refersTo="#term-operator" id="trm181">operator</term> or owner to immediately cease the operation of the <term refersTo="#term-fuel_burning_equipment" id="trm182">fuel-burning equipment</term> until such time that the <term refersTo="#term-fuel_burning_equipment" id="trm183">fuel-burning equipment</term> has been repaired to the satisfaction of the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-14.3">
            <num>(3)</num>
            <content>
              <p>Failure to comply with an order issued in terms of subsection (2) shall constitute an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-15">
          <num>15.</num>
          <heading>Installation and operation of <term refersTo="#term-obscuration" id="trm184">obscuration</term> measuring equipment</heading>
          <subsection id="section-15.1">
            <num>(1)</num>
            <content>
              <blockList id="section-15.1.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm185">authorised official</term> may give notice to any <term refersTo="#term-operator" id="trm186">operator</term> of <term refersTo="#term-fuel_burning_equipment" id="trm187">fuel-burning equipment</term>, or any owner or occupier of <term refersTo="#term-premises" id="trm188">premises</term> on which <term refersTo="#term-fuel_burning_equipment" id="trm189">fuel-burning equipment</term> is used or operated, or intended to be used or operated, to install, maintain and operate <term refersTo="#term-obscuration" id="trm190">obscuration</term> measuring equipment at his or her own cost, if -</listIntroduction>
                <item id="section-15.1.list0.a">
                  <num>(a)</num>
                  <p>unauthorised and unlawful emissions of <term refersTo="#term-dark_smoke" id="trm191">dark smoke</term> from the <term refersTo="#term-premises" id="trm192">premises</term> in question have occurred consistently and regularly over a period of at least two days;</p>
                </item>
                <item id="section-15.1.list0.b">
                  <num>(b)</num>
                  <p>unauthorised and unlawful emissions of <term refersTo="#term-dark_smoke" id="trm193">dark smoke</term> from the relevant <term refersTo="#term-premises" id="trm194">premises</term> have occurred intermittently over a period of at least fourteen days;</p>
                </item>
                <item id="section-15.1.list0.c">
                  <num>(c)</num>
                  <p><term refersTo="#term-fuel_burning_equipment" id="trm195">fuel-burning equipment</term> has been, or is intended to be, installed on the <term refersTo="#term-premises" id="trm196">premises</term> in question which is reasonably likely to emit <term refersTo="#term-dark_smoke" id="trm197">dark smoke</term>;</p>
                </item>
                <item id="section-15.1.list0.d">
                  <num>(d)</num>
                  <p>the <term refersTo="#term-person" id="trm198">person</term> on whom the notice is served has been convicted or paid an admission of guilt fine on more than one occasion in the preceding two years for a contravention committed under this Chapter or any previous by-law dealing with air quality matters and has not taken adequate measures to prevent further contravention of the provisions of this Chapter; or</p>
                </item>
                <item id="section-15.1.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm199">authorised official</term> considers that the nature of the air pollutants emitted from the relevant <term refersTo="#term-premises" id="trm200">premises</term> is reasonably likely to pose a risk to human health or the <term refersTo="#term-environment" id="trm201">environment</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-16">
          <num>16.</num>
          <heading>Monitoring and sampling</heading>
          <paragraph id="section-16.paragraph0">
            <content>
              <blockList id="section-16.paragraph0.list0">
                <listIntroduction>An occupier or owner of <term refersTo="#term-premises" id="trm202">premises</term>, and the <term refersTo="#term-operator" id="trm203">operator</term> of any <term refersTo="#term-fuel_burning_equipment" id="trm204">fuel-burning equipment</term>, who is required to install <term refersTo="#term-obscuration" id="trm205">obscuration</term> measuring equipment in terms of <ref href="#section-15">section 15</ref>(1) must -</listIntroduction>
                <item id="section-16.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>record all monitoring and sampling results and maintain a copy of this record for at least four years after obtaining the results;</p>
                </item>
                <item id="section-16.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-16.paragraph0.list0.b.list0">
                    <listIntroduction>if requested to do so by an <term refersTo="#term-authorised_official" id="trm206">authorised official</term> -</listIntroduction>
                    <item id="section-16.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p>produce the record of the monitoring and sampling results for inspection; and</p>
                    </item>
                    <item id="section-16.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p>provide a written report, in a form and by a date specified by the <term refersTo="#term-authorised_official" id="trm207">authorised official</term>, of part or all of the information in the record of the monitoring and sampling results.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </paragraph>
        </section>
        <section id="section-17">
          <num>17.</num>
          <heading>Temporary exemption</heading>
          <subsection id="section-17.1">
            <num>(1)</num>
            <content>
              <p>Subject to <ref href="#section-31">section 31</ref> and upon receipt of a fully motivated application in writing by the owner or occupier of premises or the operator of fuel-burning equipment, the City may grant a temporary exemption in writing from one or all the provisions of this Chapter.</p>
            </content>
          </subsection>
          <subsection id="section-17.2">
            <num>(2)</num>
            <content>
              <blockList id="section-17.2.list0">
                <listIntroduction>Any exemption granted under subsection (1) must state at least the following:</listIntroduction>
                <item id="section-17.2.list0.a">
                  <num>(a)</num>
                  <p>a description of the <term refersTo="#term-fuel_burning_equipment" id="trm208">fuel-burning equipment</term> and the <term refersTo="#term-premises" id="trm209">premises</term> on which it is used or operated;</p>
                </item>
                <item id="section-17.2.list0.b">
                  <num>(b)</num>
                  <p>the reasons for granting the exemption;</p>
                </item>
                <item id="section-17.2.list0.c">
                  <num>(c)</num>
                  <p>the conditions attached to the exemption, if any;</p>
                </item>
                <item id="section-17.2.list0.d">
                  <num>(d)</num>
                  <p>the period for which the exemption has been granted; and</p>
                </item>
                <item id="section-17.2.list0.e">
                  <num>(e)</num>
                  <p>any other relevant information.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-17.3">
            <num>(3)</num>
            <content>
              <blockList id="section-17.3.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm210">City</term> may not grant a temporary exemption under subsection (1) until it has:</listIntroduction>
                <item id="section-17.3.list0.a">
                  <num>(a)</num>
                  <p>taken reasonable measures to ensure that all persons whose rights may be detrimentally affected by the granting of the temporary exemption, including adjacent land owners or occupiers, are aware of the application for temporary exemption and how to obtain a copy of it;</p>
                </item>
                <item id="section-17.3.list0.b">
                  <num>(b)</num>
                  <p>provided such persons with a reasonable opportunity to object to the application; and</p>
                </item>
                <item id="section-17.3.list0.c">
                  <num>(c)</num>
                  <p>duly considered and taken into account any objections raised.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VI">
        <num>VI</num>
        <heading>Smoke emissions from dwellings</heading>
        <section id="section-18">
          <num>18.</num>
          <heading>Prohibition of emission of <term refersTo="#term-dark_smoke" id="trm211">dark smoke</term> from dwellings</heading>
          <subsection id="section-18.1">
            <num>(1)</num>
            <content>
              <p>Subject to <ref href="#section-4">section 4</ref>(1), no person shall emit or permit the emission of dark smoke from any dwelling for an aggregate period exceeding three minutes during any continuous period of thirty minutes.</p>
            </content>
          </subsection>
          <subsection id="section-18.2">
            <num>(2)</num>
            <content>
              <p>Subject to <ref href="#section-31">section 31</ref>, and on application in writing by the owner or occupier of any dwelling, the City may grant a temporary exemption in writing from one or all of the provisions of this Chapter.</p>
            </content>
          </subsection>
          <subsection id="section-18.3">
            <num>(3)</num>
            <content>
              <p>Subject to <ref href="#section-4">section 4</ref>(1), no person shall emit or permit the emission of dark smoke so as to cause a nuisance.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VII">
        <num>VII</num>
        <heading>Emissions caused by <term refersTo="#term-open_burning" id="trm212">open burning</term></heading>
        <section id="section-19">
          <num>19.</num>
          <heading>Authorisation of <term refersTo="#term-open_burning" id="trm213">open burning</term> and burning of material</heading>
          <subsection id="section-19.1">
            <num>(1)</num>
            <content>
              <p>Subject to subsection (4), no <term refersTo="#term-person" id="trm214">person</term> may carry out <term refersTo="#term-open_burning" id="trm215">open burning</term> of any material on any land or <term refersTo="#term-premises" id="trm216">premises</term>, unless such <term refersTo="#term-person" id="trm217">person</term> has first obtained written authorisation for <term refersTo="#term-open_burning" id="trm218">open burning</term> from the <term refersTo="#term-City" id="trm219">City</term>.</p>
            </content>
          </subsection>
          <subsection id="section-19.2">
            <num>(2)</num>
            <content>
              <blockList id="section-19.2.list0">
                <item id="section-19.2.list0.a">
                  <num>(a)</num>
                  <p>Where a third party wishes to conduct <term refersTo="#term-open_burning" id="trm220">open burning</term> on behalf of the owner of a property, written permission must be obtained by the third party from the owner prior to making application to the <term refersTo="#term-City" id="trm221">City</term> for authorisation to conduct <term refersTo="#term-open_burning" id="trm222">open burning</term>.</p>
                </item>
                <item id="section-19.2.list0.b">
                  <num>(b)</num>
                  <p>The <term refersTo="#term-City" id="trm223">City</term> may undertake <term refersTo="#term-open_burning" id="trm224">open burning</term> where it is reasonably necessary and where the owner or occupier cannot be contacted.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.3">
            <num>(3)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm225">City</term> may, in the written authorisation referred to in subsection (1) impose conditions with which the <term refersTo="#term-person" id="trm226">person</term> requesting written authorisation must comply.</p>
            </content>
          </subsection>
          <subsection id="section-19.4">
            <num>(4)</num>
            <content>
              <blockList id="section-19.4.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm227">City</term> may not authorise <term refersTo="#term-open_burning" id="trm228">open burning</term> referred to in subsection (1) unless it is satisfied that the applicant has adequately addressed or fulfilled the following requirements:</listIntroduction>
                <item id="section-19.4.list0.a">
                  <num>(a)</num>
                  <p>the material will be open burned on the land from which it originated;</p>
                </item>
                <item id="section-19.4.list0.b">
                  <num>(b)</num>
                  <p>the <term refersTo="#term-person" id="trm229">person</term> requesting authorisation has investigated and assessed every reasonable alternative for reducing, reusing , recycling or removing the material in order to minimize the amount of material to be open burned, to the satisfaction of the <term refersTo="#term-City" id="trm230">City</term>;</p>
                </item>
                <item id="section-19.4.list0.c">
                  <num>(c)</num>
                  <p>the <term refersTo="#term-person" id="trm231">person</term> requesting authorisation has investigated and assessed the impact the <term refersTo="#term-open_burning" id="trm232">open burning</term> will have on the <term refersTo="#term-environment" id="trm233">environment</term> to the satisfaction of the <term refersTo="#term-City" id="trm234">City</term>;</p>
                </item>
                <item id="section-19.4.list0.d">
                  <num>(d)</num>
                  <blockList id="section-19.4.list0.d.list0">
                    <listIntroduction>the <term refersTo="#term-person" id="trm235">person</term> requesting authorisation has either placed a notice in a local newspaper circulating in the area or notified in writing the owners and or occupiers of all adjacent properties of –</listIntroduction>
                    <item id="section-19.4.list0.d.list0.i">
                      <num>(i)</num>
                      <p>all known details of the proposed <term refersTo="#term-open_burning" id="trm236">open burning</term>; and</p>
                    </item>
                    <item id="section-19.4.list0.d.list0.ii">
                      <num>(ii)</num>
                      <p>the right of owners and occupiers of adjacent properties to lodge written objections to the proposed <term refersTo="#term-open_burning" id="trm237">open burning</term> with the <term refersTo="#term-City" id="trm238">City</term> within seven days of being notified;</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-19.4.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-person" id="trm239">person</term> requesting authorisation has provided proof that the written notification was received by the owners and or occupiers of all adjacent properties at least seven (7) days prior to the <term refersTo="#term-open_burning" id="trm240">open burning</term> application being considered;</p>
                </item>
                <item id="section-19.4.list0.f">
                  <num>(f)</num>
                  <p>the prescribed fee has been paid to the <term refersTo="#term-City" id="trm241">City</term>;</p>
                </item>
                <item id="section-19.4.list0.g">
                  <num>(g)</num>
                  <p>the land on which that <term refersTo="#term-person" id="trm242">person</term> intends to open burn the material is state land, a farm or small-holding, or land within a proclaimed township that is not utilised for residential purposes;</p>
                </item>
                <item id="section-19.4.list0.h">
                  <num>(h)</num>
                  <p>the <term refersTo="#term-open_burning" id="trm243">open burning</term> is conducted at least 100 metres from any buildings or structures; and</p>
                </item>
                <item id="section-19.4.list0.i">
                  <num>(i)</num>
                  <p>the <term refersTo="#term-open_burning" id="trm244">open burning</term> will not pose a potential hazard to human health or safety, private property or to the <term refersTo="#term-environment" id="trm245">environment</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.5">
            <num>(5)</num>
            <content>
              <blockList id="section-19.5.list0">
                <listIntroduction>The provisions of this section shall not apply to -</listIntroduction>
                <item id="section-19.5.list0.a">
                  <num>(a)</num>
                  <p>recreational outdoor barbecue or braai activities on private <term refersTo="#term-premises" id="trm246">premises</term> or in designated spaces;</p>
                </item>
                <item id="section-19.5.list0.b">
                  <num>(b)</num>
                  <p>small controlled fires in informal settlements for the purposes of cooking, heating water and other domestic purposes;</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.6">
            <num>(6)</num>
            <content>
              <p>For the purposes of fire safety training sections (4)(a), (b), (f) and (g) shall not apply.</p>
            </content>
          </subsection>
          <subsection id="section-19.7">
            <num>(7)</num>
            <content>
              <p>The management practices set out in schedule 2 to the By-law must be applied to prevent or minimise the discharge of <term refersTo="#term-smoke" id="trm247">smoke</term> from <term refersTo="#term-open_burning" id="trm248">open burning</term> of vegetation within the <term refersTo="#term-City" id="trm249">City</term>’s jurisdiction.</p>
            </content>
          </subsection>
        </section>
        <section id="section-20">
          <num>20.</num>
          <heading>Emissions caused by tyre burning and burning of rubber and other material for the recovery of metal</heading>
          <subsection id="section-20.1">
            <num>(1)</num>
            <content>
              <blockList id="section-20.1.list0">
                <listIntroduction>No <term refersTo="#term-person" id="trm250">person</term> may, without prior written authorisation by the <term refersTo="#term-City" id="trm251">City</term>, on any <term refersTo="#term-premises" id="trm252">premises</term> –</listIntroduction>
                <item id="section-20.1.list0.a">
                  <num>(a)</num>
                  <blockList id="section-20.1.list0.a.list0">
                    <listIntroduction>carry out or permit the burning of any tyres, rubber products, cables, synthetically covered or insulated products, equipment or any other similar product for purposes of</listIntroduction>
                    <item id="section-20.1.list0.a.list0.i">
                      <num>(i)</num>
                      <p>recovering the metal contained therein;</p>
                    </item>
                    <item id="section-20.1.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>disposing of tyres or any other product described in (a) above as waste; or</p>
                    </item>
                    <item id="section-20.1.list0.a.list0.iii">
                      <num>(iii)</num>
                      <p>for any other reason, except for the thermal treatment of general and hazardous waste in any device licensed in terms of section 41(1)(a) of the National Environmental Management: <term refersTo="#term-Air_Quality_Act" id="trm253">Air Quality Act</term>;</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-20.1.list0.b">
                  <num>(b)</num>
                  <p>possess, store, transport or trade in any <term refersTo="#term-burnt_metal" id="trm254">burnt metal</term> recovered as a result of <term refersTo="#term-unauthorised_burning" id="trm255">unauthorised burning</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-20.2">
            <num>(2)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm256">authorised official</term> may for the purpose of gathering evidence, seize any <term refersTo="#term-burnt_metal" id="trm257">burnt metal</term> or metal in the process of being burnt where authorisation in terms of <ref href="#section-20">section 20</ref>(1) has not been obtained or cannot be provided by a person referred to in that subsection.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VIII">
        <num>VIII</num>
        <heading>Emissions from compression ignition powered vehicles</heading>
        <section id="section-21">
          <num>21.</num>
          <heading>Prohibition of <term refersTo="#term-dark_smoke" id="trm258">dark smoke</term> from compression ignition powered vehicles</heading>
          <subsection id="section-21.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm259">person</term> may on a public or private road or any <term refersTo="#term-premises" id="trm260">premises</term> drive or use, or cause to be used, a <term refersTo="#term-compression_ignition_powered_vehicle" id="trm261">compression ignition powered vehicle</term> that emits <term refersTo="#term-dark_smoke" id="trm262">dark smoke</term>.</p>
            </content>
          </subsection>
          <subsection id="section-21.2">
            <num>(2)</num>
            <content>
              <p>For purposes of this Chapter the registered owner of the <term refersTo="#term-vehicle" id="trm263">vehicle</term> shall be presumed to be the driver unless the contrary is proven.</p>
            </content>
          </subsection>
        </section>
        <section id="section-22">
          <num>22.</num>
          <heading>Stopping of vehicles for inspection and testing</heading>
          <subsection id="section-22.1">
            <num>(1)</num>
            <content>
              <p>In order to enable an <term refersTo="#term-authorised_official" id="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" id="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" id="trm266">vehicle</term>.</p>
            </content>
          </subsection>
          <subsection id="section-22.2">
            <num>(2)</num>
            <content>
              <blockList id="section-22.2.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" id="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" id="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" id="trm270">vehicle</term> in order to -</listIntroduction>
                <item id="section-22.2.list0.a">
                  <num>(a)</num>
                  <blockList id="section-22.2.list0.a.list0">
                    <listIntroduction>inspect and test the <term refersTo="#term-vehicle" id="trm271">vehicle</term> at the roadside, in which case inspection and testing must be carried out -</listIntroduction>
                    <item id="section-22.2.list0.a.list0.i">
                      <num>(i)</num>
                      <p>at or as near as practicable to the place where the direction to stop the <term refersTo="#term-vehicle" id="trm272">vehicle</term> is given; and</p>
                    </item>
                    <item id="section-22.2.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>as soon as practicable, and in any case within one hour, after the <term refersTo="#term-vehicle" id="trm273">vehicle</term> is stopped in accordance with the direction; or</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-22.2.list0.b">
                  <num>(b)</num>
                  <p>conduct a visual inspection of the <term refersTo="#term-vehicle" id="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#section-21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#section-23">section 23</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-23">
          <num>23.</num>
          <heading>Testing procedure</heading>
          <subsection id="section-23.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" id="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" id="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#section-21">section 21</ref>(1).</p>
            </content>
          </subsection>
          <subsection id="section-23.2">
            <num>(2)</num>
            <content>
              <blockList id="section-23.2.list0">
                <listIntroduction>The following procedure must be adhered to in order to conduct a <term refersTo="#term-free_acceleration_test" id="trm278">free acceleration test</term>:</listIntroduction>
                <item id="section-23.2.list0.a">
                  <num>(a)</num>
                  <p>when instructed to do so by the <term refersTo="#term-authorised_official" id="trm279">authorised official</term>, the driver must start the <term refersTo="#term-vehicle" id="trm280">vehicle</term>, place it in neutral gear and engage the clutch;</p>
                </item>
                <item id="section-23.2.list0.b">
                  <num>(b)</num>
                  <p>while the <term refersTo="#term-vehicle" id="trm281">vehicle</term> is idling, the <term refersTo="#term-authorised_official" id="trm282">authorised official</term> must conduct a visual inspection of the emission system of the <term refersTo="#term-vehicle" id="trm283">vehicle</term>;</p>
                </item>
                <item id="section-23.2.list0.c">
                  <num>(c)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm284">authorised official</term> must rapidly, smoothly and completely depress the accelerator throttle pedal of the <term refersTo="#term-vehicle" id="trm285">vehicle</term>, or he may instruct the driver to do likewise under his supervision;</p>
                </item>
                <item id="section-23.2.list0.d">
                  <num>(d)</num>
                  <p>while the throttle pedal is depressed, the <term refersTo="#term-authorised_official" id="trm286">authorised official</term> must measure the <term refersTo="#term-smoke" id="trm287">smoke</term> emitted from the emission system of the <term refersTo="#term-vehicle" id="trm288">vehicle</term> in order to determine whether or not it is <term refersTo="#term-dark_smoke" id="trm289">dark smoke</term>;</p>
                </item>
                <item id="section-23.2.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm290">authorised official</term> must release the throttle pedal when the engine reaches cut-off speed;</p>
                </item>
                <item id="section-23.2.list0.f">
                  <num>(f)</num>
                  <p>if the <term refersTo="#term-authorised_official" id="trm291">authorised official</term> instructs the driver to depress the throttle, the driver may only release the throttle when it reaches cut-off speed or when instructed to do so by the <term refersTo="#term-authorised_official" id="trm292">authorised official</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-23.3">
            <num>(3)</num>
            <content>
              <blockList id="section-23.3.list0">
                <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" id="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" id="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" id="trm295">vehicle</term> -</listIntroduction>
                <item id="section-23.3.list0.a">
                  <num>(a)</num>
                  <p>is not emitting <term refersTo="#term-dark_smoke" id="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" id="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" id="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#section-21">section 21</ref>; or</p>
                </item>
                <item id="section-23.3.list0.b">
                  <num>(b)</num>
                  <p>is emitting <term refersTo="#term-dark_smoke" id="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" id="trm300">vehicle</term> with a repair notice in accordance with <ref href="#section-24">section 24</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-24">
          <num>24.</num>
          <heading>Repair notice</heading>
          <subsection id="section-24.1">
            <num>(1)</num>
            <content>
              <p>In the event that a determination is made in terms of <ref href="#section-23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
            </content>
          </subsection>
          <subsection id="section-24.2">
            <num>(2)</num>
            <content>
              <p>A copy of the test results must be provided by the registered owner of the <term refersTo="#term-vehicle" id="trm301">vehicle</term> or his representative to the authorised official where the testing station is not a <term refersTo="#term-City" id="trm302">City</term> testing facility on or before the due date of the repair notice.</p>
            </content>
          </subsection>
          <subsection id="section-24.3">
            <num>(3)</num>
            <content>
              <blockList id="section-24.3.list0">
                <listIntroduction>The repair notice must contain the following information:</listIntroduction>
                <item id="section-24.3.list0.a">
                  <num>(a)</num>
                  <p>the make and registration number of the <term refersTo="#term-vehicle" id="trm303">vehicle</term>;</p>
                </item>
                <item id="section-24.3.list0.b">
                  <num>(b)</num>
                  <p>the name, address and identity number of the driver of the <term refersTo="#term-vehicle" id="trm304">vehicle</term>; and</p>
                </item>
                <item id="section-24.3.list0.c">
                  <num>(c)</num>
                  <p>if the driver is not the owner of the <term refersTo="#term-vehicle" id="trm305">vehicle</term>, the name and address of the <term refersTo="#term-vehicle" id="trm306">vehicle</term> owner.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-24.4">
            <num>(4)</num>
            <content>
              <p>The owner of a <term refersTo="#term-vehicle" id="trm307">vehicle</term> is deemed to have been notified of the repair notice on the date that such notice is issued.</p>
            </content>
          </subsection>
          <subsection id="section-24.5">
            <num>(5)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm308">City</term> may take whatever steps it considers necessary in the event that the requirements of subsection (1) are not complied with, including impounding the <term refersTo="#term-vehicle" id="trm309">vehicle</term> and recovering any costs incurred in that regard from the owner of the <term refersTo="#term-vehicle" id="trm310">vehicle</term>.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-IX">
        <num>IX</num>
        <heading>Emissions that cause a <term refersTo="#term-nuisance" id="trm311">nuisance</term></heading>
        <section id="section-25">
          <num>25.</num>
          <heading>Prohibition of emissions that cause <term refersTo="#term-nuisance" id="trm312">nuisance</term></heading>
          <subsection id="section-25.1">
            <num>(1)</num>
            <content>
              <blockList id="section-25.1.list0">
                <listIntroduction>No <term refersTo="#term-person" id="trm313">person</term> shall, within the area of jurisdiction of the <term refersTo="#term-City" id="trm314">City</term> of Cape Town-</listIntroduction>
                <item id="section-25.1.list0.a">
                  <num>(a)</num>
                  <p>spray or apply any coat, plate or epoxy coat to any <term refersTo="#term-vehicle" id="trm315">vehicle</term>, article or object, inside an approved <term refersTo="#term-spray_area" id="trm316">spray area</term> or spray booth, so as to cause a <term refersTo="#term-nuisance" id="trm317">nuisance</term>; or</p>
                </item>
                <item id="section-25.1.list0.b">
                  <num>(b)</num>
                  <p>spray, coat, plate or epoxy coat to be applied to any such <term refersTo="#term-vehicle" id="trm318">vehicle</term>, article or object or allow it to be sprayed, coated plated or epoxy coated or similar activity outside an approved <term refersTo="#term-spray_area" id="trm319">spray area</term> or spray booth.</p>
                </item>
                <item id="section-25.1.list0.c">
                  <num>(c)</num>
                  <blockList id="section-25.1.list0.c.list0">
                    <listIntroduction>cause any unreasonable interference or likely interference through <term refersTo="#term-air_pollution" id="trm320">air pollution</term>, which may adversely affect -</listIntroduction>
                    <item id="section-25.1.list0.c.list0.i">
                      <num>(i)</num>
                      <p>the health or well-being of any <term refersTo="#term-person" id="trm321">person</term> or <term refersTo="#term-living_organism" id="trm322">living organism</term>; or</p>
                    </item>
                    <item id="section-25.1.list0.c.list0.ii">
                      <num>(ii)</num>
                      <p>the use and enjoyment by an owner or occupier of his or her property or <term refersTo="#term-environment" id="trm323">environment</term>;</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.2">
            <num>(2)</num>
            <content>
              <blockList id="section-25.2.list0">
                <listIntroduction>Any <term refersTo="#term-spray_area" id="trm324">spray area</term> or spray booth referred to in subsection (1) must be:</listIntroduction>
                <item id="section-25.2.list0.a">
                  <num>(a)</num>
                  <p>constructed and equipped in accordance with the General Safety Regulations promulgated in terms of the Occupational Health and Safety Act, 1993 (<ref href="/za/act/1993/85">Act No. 85 of 1993</ref>); and</p>
                </item>
                <item id="section-25.2.list0.b">
                  <num>(b)</num>
                  <p>approved by the <term refersTo="#term-authorised_official" id="trm325">authorised official</term>, for emissions, mechanical ventilation, noise and any other relevant Department as may be required by any other law.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.3">
            <num>(3)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm326">person</term> conducting sand blasting, shot blasting, grinding, finishing or similar activity which customarily produces emissions of <term refersTo="#term-dust" id="trm327">dust</term> that may be harmful to public health, or cause a <term refersTo="#term-nuisance" id="trm328">nuisance</term>, shall take the <term refersTo="#term-best_practicable_environmental_option" id="trm329">best practicable environmental option</term> to prevent emissions into the <term refersTo="#term-atmosphere" id="trm330">atmosphere</term> to the satisfaction of the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-25.4">
            <num>(4)</num>
            <content>
              <blockList id="section-25.4.list0">
                <listIntroduction>Any <term refersTo="#term-person" id="trm331">person</term> undertaking an activity referred to in subsection (3) must implement at least the following control measures:</listIntroduction>
                <item id="section-25.4.list0.a">
                  <num>(a)</num>
                  <p><term refersTo="#term-dust" id="trm332">dust</term> extraction control measures;</p>
                </item>
                <item id="section-25.4.list0.b">
                  <num>(b)</num>
                  <p>any alternative control measure approved by the <term refersTo="#term-air_quality_officer" id="trm333">air quality officer</term> or his or he delegated representative.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.5">
            <num>(5)</num>
            <content>
              <p>An occupier or owner of any <term refersTo="#term-premises" id="trm334">premises</term> must prevent the existence in, or emission of any <term refersTo="#term-air_pollution" id="trm335">air pollution</term> <term refersTo="#term-nuisance" id="trm336">nuisance</term> from, his or her <term refersTo="#term-premises" id="trm337">premises</term>.</p>
            </content>
          </subsection>
          <subsection id="section-25.6">
            <num>(6)</num>
            <content>
              <p>The occupier or owner of any <term refersTo="#term-premises" id="trm338">premises</term> from which an <term refersTo="#term-air_pollution" id="trm339">air pollution</term> <term refersTo="#term-nuisance" id="trm340">nuisance</term> emanates, or where an <term refersTo="#term-air_pollution" id="trm341">air pollution</term> <term refersTo="#term-nuisance" id="trm342">nuisance</term> exists, is guilty of an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-26">
          <num>26.</num>
          <heading>Dust emissions</heading>
          <subsection id="section-26.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm343">person</term> who conducts any activity or omits to conduct any activity which causes or permits <term refersTo="#term-dust" id="trm344">dust</term> emissions into the <term refersTo="#term-atmosphere" id="trm345">atmosphere</term> that may be harmful to public health and well-being or is likely to cause a <term refersTo="#term-nuisance" id="trm346">nuisance</term> to persons residing or present in the vicinity of such land, activity or <term refersTo="#term-premises" id="trm347">premises</term> shall adopt the best practical environmental option to the satisfaction of the authorised official, to prevent and abate <term refersTo="#term-dust" id="trm348">dust</term> emissions.</p>
            </content>
          </subsection>
          <subsection id="section-26.2">
            <num>(2)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm349">authorised official</term> may require any <term refersTo="#term-person" id="trm350">person</term> suspected of causing a <term refersTo="#term-dust" id="trm351">dust</term> <term refersTo="#term-nuisance" id="trm352">nuisance</term> to submit a <term refersTo="#term-dust" id="trm353">dust</term> management plan within the time period specified in the written notice.</p>
            </content>
          </subsection>
          <subsection id="section-26.3">
            <num>(3)</num>
            <content>
              <blockList id="section-26.3.list0">
                <listIntroduction>The <term refersTo="#term-dust" id="trm354">dust</term> management plan contemplated in subsection (2) must:</listIntroduction>
                <item id="section-26.3.list0.a">
                  <num>(a)</num>
                  <p>identify all possible sources of <term refersTo="#term-dust" id="trm355">dust</term> within the affected site;</p>
                </item>
                <item id="section-26.3.list0.b">
                  <num>(b)</num>
                  <p>detail the best practicable measures to be undertaken to mitigate <term refersTo="#term-dust" id="trm356">dust</term> emissions;</p>
                </item>
                <item id="section-26.3.list0.c">
                  <num>(c)</num>
                  <p>detail an implementation schedule;</p>
                </item>
                <item id="section-26.3.list0.d">
                  <num>(d)</num>
                  <p>identify the <term refersTo="#term-person" id="trm357">person</term> responsible for implementation of the measures;</p>
                </item>
                <item id="section-26.3.list0.e">
                  <num>(e)</num>
                  <p>incorporate a dustfall monitoring plan; and</p>
                </item>
                <item id="section-26.3.list0.f">
                  <num>(f)</num>
                  <p>establish a register for recording all complaints received by the persons regarding dustfall, and for recording follow up actions and responses to the complaints.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-26.4">
            <num>(4)</num>
            <content>
              <p>The <term refersTo="#term-authorised_official" id="trm358">authorised official</term> may require additional measures to be detailed in the <term refersTo="#term-dust" id="trm359">dust</term> management plan.</p>
            </content>
          </subsection>
          <subsection id="section-26.5">
            <num>(5)</num>
            <content>
              <p>The <term refersTo="#term-dust" id="trm360">dust</term> management plan must be implemented within a time period specified by the authorised official in a written notice.</p>
            </content>
          </subsection>
          <subsection id="section-26.6">
            <num>(6)</num>
            <content>
              <p>Failure to comply with the provisions of this section constitutes an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-27">
          <num>27.</num>
          <heading>Steps to abate <term refersTo="#term-nuisance" id="trm361">nuisance</term></heading>
          <paragraph id="section-27.paragraph0">
            <content>
              <p>At any time, the <term refersTo="#term-City" id="trm362">City</term> may at its own cost take whatever steps it considers necessary in order to remedy the harm caused by the <term refersTo="#term-nuisance" id="trm363">nuisance</term> and prevent a recurrence of it, and may recover the reasonable costs incurred from the <term refersTo="#term-person" id="trm364">person</term> responsible for causing the <term refersTo="#term-nuisance" id="trm365">nuisance</term>.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-X">
        <num>X</num>
        <heading>General matters</heading>
        <section id="section-28">
          <num>28.</num>
          <heading>Compliance notice</heading>
          <subsection id="section-28.1">
            <num>(1)</num>
            <content>
              <blockList id="section-28.1.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm366">authorised official</term> may serve a compliance notice on any <term refersTo="#term-person" id="trm367">person</term> whom he or she reasonably believes is likely to act contrary to, or has acted in contravention of the By-law, calling upon that <term refersTo="#term-person" id="trm368">person</term> -</listIntroduction>
                <item id="section-28.1.list0.a">
                  <num>(a)</num>
                  <p>to comply with the relevant section of the By-law;</p>
                </item>
                <item id="section-28.1.list0.b">
                  <num>(b)</num>
                  <p>to take all necessary steps to prevent a recurrence of the non-compliance; and</p>
                </item>
                <item id="section-28.1.list0.c">
                  <num>(c)</num>
                  <p>to comply with any other conditions contained in the notice.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-28.2">
            <num>(2)</num>
            <content>
              <blockList id="section-28.2.list0">
                <listIntroduction>A compliance notice under subsection (1) may be served -</listIntroduction>
                <item id="section-28.2.list0.a">
                  <num>(a)</num>
                  <blockList id="section-28.2.list0.a.list0">
                    <listIntroduction>upon the occupier, manager or owner of any <term refersTo="#term-premises" id="trm369">premises</term>, by -</listIntroduction>
                    <item id="section-28.2.list0.a.list0.i">
                      <num>(i)</num>
                      <p>delivering it to the occupier, manager or owner or, if the owner cannot be traced or is living abroad, the agent of the owner;</p>
                    </item>
                    <item id="section-28.2.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>transmitting it by registered post to the last known address of the owner or the last known address of the agent; or</p>
                    </item>
                    <item id="section-28.2.list0.a.list0.iii">
                      <num>(iii)</num>
                      <p>delivering it to the address where the <term refersTo="#term-premises" id="trm370">premises</term> are situated, if the address of the owner and the address of the agent are unknown;</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-28.3">
            <num>(3)</num>
            <content>
              <p>Failure to comply with a compliance notice constitutes an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-29">
          <num>29.</num>
          <heading>Enforcement</heading>
          <subsection id="section-29.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm371">authorised official</term> must take all lawful, necessary and reasonable practicable measures to enforce the provisions of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-29.2">
            <num>(2)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm372">City</term> may develop enforcement procedures which should take into consideration any national or provincial enforcement procedures.</p>
            </content>
          </subsection>
        </section>
        <section id="section-30">
          <num>30.</num>
          <heading>Appeals</heading>
          <subsection id="section-30.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm373">person</term> may appeal against a decision taken by an authorised official under this By-law by giving a written notice of the appeal in accordance with the provisions of section 62 of the <term refersTo="#term-Municipal_Systems_Act" id="trm374">Municipal Systems Act</term>.</p>
            </content>
          </subsection>
        </section>
        <section id="section-31">
          <num>31.</num>
          <heading>Exemptions</heading>
          <subsection id="section-31.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm375">person</term> may apply to the <term refersTo="#term-City" id="trm376">City</term>, in writing, for exemption from the application of a provision of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-31.2">
            <num>(2)</num>
            <content>
              <blockList id="section-31.2.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm377">City</term> may-</listIntroduction>
                <item id="section-31.2.list0.a">
                  <num>(a)</num>
                  <p>approve or refuse an application for exemption; and</p>
                </item>
                <item id="section-31.2.list0.b">
                  <num>(b)</num>
                  <p>impose conditions when granting approval for applications for exemption, made in terms of subsection (1).</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.3">
            <num>(3)</num>
            <content>
              <p>An application in terms of subsection (1) must be accompanied by substantive reasons.</p>
            </content>
          </subsection>
          <subsection id="section-31.4">
            <num>(4)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm378">City</term> may require an applicant applying for exemption to take appropriate steps to bring the application to the attention of relevant interested and affected persons and the public.</p>
            </content>
          </subsection>
          <subsection id="section-31.5">
            <num>(5)</num>
            <content>
              <blockList id="section-31.5.list0">
                <listIntroduction>The steps contemplated in subsection (4) must include the publication of a notice in at least two newspapers, one circulating provincially and one circulating within the jurisdiction of the <term refersTo="#term-City" id="trm379">City</term>-</listIntroduction>
                <item id="section-31.5.list0.a">
                  <num>(a)</num>
                  <p>giving reasons for the application; and</p>
                </item>
                <item id="section-31.5.list0.b">
                  <num>(b)</num>
                  <p>containing such other particulars concerning the application as the <term refersTo="#term-air_quality_officer" id="trm380">air quality officer</term> may require.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.6">
            <num>(6)</num>
            <content>
              <blockList id="section-31.6.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm381">City</term> may -</listIntroduction>
                <item id="section-31.6.list0.a">
                  <num>(a)</num>
                  <p>from time to time review any exemption granted in terms of this section, and may impose such conditions as it may determine; and</p>
                </item>
                <item id="section-31.6.list0.b">
                  <num>(b)</num>
                  <p>on good grounds withdraw any exemption.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.7">
            <num>(7)</num>
            <content>
              <blockList id="section-31.7.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm382">City</term> may not grant an exemption under subsection (1) until the <term refersTo="#term-City" id="trm383">City</term> has:</listIntroduction>
                <item id="section-31.7.list0.a">
                  <num>(a)</num>
                  <p>taken reasonable measures to ensure that all persons whose rights may be detrimentally affected by the granting of the exemption, including adjacent land owners or occupiers, are aware of the application for exemption.</p>
                </item>
                <item id="section-31.7.list0.b">
                  <num>(b)</num>
                  <p>provided such persons with a reasonable opportunity to object to the application; and</p>
                </item>
                <item id="section-31.7.list0.c">
                  <num>(c)</num>
                  <p>duly considered and taken into account any reasonable objections raised.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-32">
          <num>32.</num>
          <heading>Indemnity</heading>
          <paragraph id="section-32.paragraph0">
            <content>
              <p>The <term refersTo="#term-City" id="trm384">City</term> shall not be liable for any damage caused to any property or <term refersTo="#term-premises" id="trm385">premises</term> by any action or omission on the part of the employees or officials of the <term refersTo="#term-City" id="trm386">City</term> when exercising any function or performing any duty in terms of this By-law, provided that such employees or officials must, when exercising such function or performing such duty, take reasonable steps to prevent any damage to such property or <term refersTo="#term-premises" id="trm387">premises</term>.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <hcontainer id="chapter-XI.crossheading-0" name="crossheading">
          <heading>First in chapter</heading>
        </hcontainer>
        <section id="section-33">
          <num>33.</num>
          <heading>Offences and penalties</heading>
          <subsection id="section-33.1">
            <num>(1)</num>
            <content>
              <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
            </content>
          </subsection>
          <subsection id="section-33.2">
            <num>(2)</num>
            <content>
              <p>Any person who is guilty of an offence in terms of this By-law is liable to a fine or, upon conviction to, imprisonment not exceeding 1 year or to both such fine and such imprisonment.</p>
            </content>
          </subsection>
          <subsection id="section-33.3">
            <num>(3)</num>
            <content>
              <p>Any person who commits a continuing offence may be liable to a fine for each day during which that person fails to comply with a directive, compliance notice or repair notice, issued in terms of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-33.4">
            <num>(4)</num>
            <content>
              <p>It is an offence to supply false information to an authorised official in respect of any issue pertaining to this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-33.5">
            <num>(5)</num>
            <content>
              <p>Where no specific penalty is provided, any person committing an offence in terms of this By-law is liable to a fine and upon conviction to imprisonment for a period not exceeding one (1) year or to both such imprisonment and such fine.</p>
            </content>
          </subsection>
          <subsection id="section-33.6">
            <num>(6)</num>
            <content>
              <blockList id="section-33.6.list0">
                <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
                <item id="section-33.6.list0.a">
                  <num>(a)</num>
                  <p>to remedy the harm caused; and</p>
                </item>
                <item id="section-33.6.list0.b">
                  <num>(b)</num>
                  <p>to pay damages for harm caused to another person or to property.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-34">
          <num>34.</num>
          <heading>Repeal and savings</heading>
          <subsection id="section-34.1">
            <num>(1)</num>
            <content>
              <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
            </content>
          </subsection>
          <subsection id="section-34.2">
            <num>(2)</num>
            <content>
              <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
            </content>
          </subsection>
          <hcontainer id="section-34.crossheading-0" name="crossheading">
            <heading>Second in chapter</heading>
          </hcontainer>
        </section>
        <section id="section-35">
          <num>35.</num>
          <heading>Short title</heading>
          <paragraph id="section-35.paragraph0">
            <content>
              <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management"/>
              <FRBRalias value="Schedule 1"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <heading>Schedule 1</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph1">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za/act/1980/01/schedule2"/>
              <FRBRuri value="/za/act/1980/01"/>
              <FRBRalias value="Schedule 2"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="2020-05-21" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>Good management practices to prevent or minimise the discharge of smoke from open burning of vegetation</subheading>
            <paragraph id="schedule2.paragraph-1">
              <num>1.</num>
              <content>
                <p>Consider alternatives to burning – e.g. mulching for recovery of nutrient value, drying for recovery as firewood.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-2">
              <num>2.</num>
              <content>
                <p>Vegetation that is to be burned (such as trimmings, pruning or felling’s cut from active growth) should as a general guide be allowed to dry to brown appearance prior to burning.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>Here's one</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-3">
              <num>3.</num>
              <content>
                <p>Except for tree stumps or crop stubble, the place of combustion should be at least 50 metres from any road other than a highway, and 100 metres from any highway or dwelling on a neighbouring property.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-4">
              <num>4.</num>
              <content>
                <p>Due regard should be given to direction and strength of wind, and quantity and state of vegetation to be combusted, prior to initiating combustion.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-5">
              <num>5.</num>
              <content>
                <p>In the case of vegetation previously treated by spray with any agrichemical, any manufacturer's instructions as on the label of any container in respect of the burning of treated vegetation must be observed.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.crossheading-1" name="crossheading">
              <heading>And another</heading>
            </hcontainer>
            <hcontainer id="schedule2.crossheading-2" name="crossheading">
              <heading>And more</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-6">
              <num>6.</num>
              <content>
                <p>Two days' fine weather should be allowed prior to burning.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-7">
              <num>7.</num>
              <content>
                <p>Vegetation should be stacked loosely rather than compacted.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-8">
              <num>8.</num>
              <content>
                <p>A small fire, started with the driest material, with further material continually fed onto it once it is blazing, is preferable to a large stack ignited and left unattended.</p>
                <p><b>Note:</b> Persons conducting open burning of vegetation must ensure compliance with the requirements of the National Veld and Forest Fire Act, 1998, (<ref href="/za/act/1998/101">Act No. 101 of 1998</ref>) as amended.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
""")
        CrossheadingToHcontainer().migrate_act(cobalt_doc, mappings)
        # UnnumberedParagraphsToHcontainer().migrate_act(cobalt_doc, mappings)
        # ComponentSchedulesToAttachments().migrate_act(cobalt_doc, mappings)
        # AKNeId().migrate_act(cobalt_doc, mappings)
        #
        # self.chain_mappings(mappings)
        #
        # HrefMigration().migrate_act(cobalt_doc, mappings)
        # AnnotationsMigration().migrate_act(cobalt_doc, mappings)
        output = cobalt_doc.to_xml().decode("utf-8")

        # check XML
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta>
      <identification source="#slaw">
        <FRBRWork>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management"/>
          <FRBRalias value="Air Quality Management"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRcountry value="za"/>
        </FRBRWork>
        <FRBRExpression>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
          <FRBRdate date="2016-08-17" name="Generation"/>
          <FRBRauthor href="#council"/>
          <FRBRlanguage language="eng"/>
        </FRBRExpression>
        <FRBRManifestation>
          <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/main"/>
          <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
          <FRBRdate date="2020-01-27" name="Generation"/>
          <FRBRauthor href="#slaw"/>
        </FRBRManifestation>
      </identification>
      <publication number="7662" name="Western Cape Provincial Gazette" showAs="Western Cape Provincial Gazette" date="2016-08-17"/>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
        <TLCTerm id="term-Air_Quality_Act" showAs="Air Quality Act" href="/ontology/term/this.eng.Air_Quality_Act"/>
        <TLCTerm id="term-adverse_effect" showAs="adverse effect" href="/ontology/term/this.eng.adverse_effect"/>
        <TLCTerm id="term-air_pollutant" showAs="air pollutant" href="/ontology/term/this.eng.air_pollutant"/>
        <TLCTerm id="term-air_pollution" showAs="air pollution" href="/ontology/term/this.eng.air_pollution"/>
        <TLCTerm id="term-air_pollution_control_zone" showAs="air pollution control zone" href="/ontology/term/this.eng.air_pollution_control_zone"/>
        <TLCTerm id="term-air_quality_management_plan" showAs="air quality management plan" href="/ontology/term/this.eng.air_quality_management_plan"/>
        <TLCTerm id="term-air_quality_officer" showAs="air quality officer" href="/ontology/term/this.eng.air_quality_officer"/>
        <TLCTerm id="term-ambient_air" showAs="ambient air" href="/ontology/term/this.eng.ambient_air"/>
        <TLCTerm id="term-atmosphere" showAs="atmosphere" href="/ontology/term/this.eng.atmosphere"/>
        <TLCTerm id="term-atmospheric_emission" showAs="atmospheric emission" href="/ontology/term/this.eng.atmospheric_emission"/>
        <TLCTerm id="term-authorised_official" showAs="authorised official" href="/ontology/term/this.eng.authorised_official"/>
        <TLCTerm id="term-best_practicable_environmental_option" showAs="best practicable environmental option" href="/ontology/term/this.eng.best_practicable_environmental_option"/>
        <TLCTerm id="term-burnt_metal" showAs="burnt metal" href="/ontology/term/this.eng.burnt_metal"/>
        <TLCTerm id="term-chimney" showAs="chimney" href="/ontology/term/this.eng.chimney"/>
        <TLCTerm id="term-City" showAs="City" href="/ontology/term/this.eng.City"/>
        <TLCTerm id="term-City_Manager" showAs="City Manager" href="/ontology/term/this.eng.City_Manager"/>
        <TLCTerm id="term-compression_ignition_powered_vehicle" showAs="compression ignition powered vehicle" href="/ontology/term/this.eng.compression_ignition_powered_vehicle"/>
        <TLCTerm id="term-continuing_offence" showAs="continuing offence" href="/ontology/term/this.eng.continuing_offence"/>
        <TLCTerm id="term-Council" showAs="Council" href="/ontology/term/this.eng.Council"/>
        <TLCTerm id="term-dark_smoke" showAs="dark smoke" href="/ontology/term/this.eng.dark_smoke"/>
        <TLCTerm id="term-directive" showAs="directive" href="/ontology/term/this.eng.directive"/>
        <TLCTerm id="term-dust" showAs="dust" href="/ontology/term/this.eng.dust"/>
        <TLCTerm id="term-dwelling" showAs="dwelling" href="/ontology/term/this.eng.dwelling"/>
        <TLCTerm id="term-environment" showAs="environment" href="/ontology/term/this.eng.environment"/>
        <TLCTerm id="term-Executive_Director__City_Health" showAs="Executive Director: City Health" href="/ontology/term/this.eng.Executive_Director__City_Health"/>
        <TLCTerm id="term-free_acceleration_test" showAs="free acceleration test" href="/ontology/term/this.eng.free_acceleration_test"/>
        <TLCTerm id="term-fuel_burning_equipment" showAs="fuel-burning equipment" href="/ontology/term/this.eng.fuel_burning_equipment"/>
        <TLCTerm id="term-light_absorption_meter" showAs="light absorption meter" href="/ontology/term/this.eng.light_absorption_meter"/>
        <TLCTerm id="term-living_organism" showAs="living organism" href="/ontology/term/this.eng.living_organism"/>
        <TLCTerm id="term-Municipal_Systems_Act" showAs="Municipal Systems Act" href="/ontology/term/this.eng.Municipal_Systems_Act"/>
        <TLCTerm id="term-nuisance" showAs="nuisance" href="/ontology/term/this.eng.nuisance"/>
        <TLCTerm id="term-obscuration" showAs="obscuration" href="/ontology/term/this.eng.obscuration"/>
        <TLCTerm id="term-open_burning" showAs="open burning" href="/ontology/term/this.eng.open_burning"/>
        <TLCTerm id="term-operator" showAs="operator" href="/ontology/term/this.eng.operator"/>
        <TLCTerm id="term-person" showAs="person" href="/ontology/term/this.eng.person"/>
        <TLCTerm id="term-premises" showAs="premises" href="/ontology/term/this.eng.premises"/>
        <TLCTerm id="term-Provincial_Government" showAs="Provincial Government" href="/ontology/term/this.eng.Provincial_Government"/>
        <TLCTerm id="term-public_road" showAs="public road" href="/ontology/term/this.eng.public_road"/>
        <TLCTerm id="term-smoke" showAs="smoke" href="/ontology/term/this.eng.smoke"/>
        <TLCTerm id="term-specialist_study" showAs="specialist study" href="/ontology/term/this.eng.specialist_study"/>
        <TLCTerm id="term-spray_area" showAs="spray area" href="/ontology/term/this.eng.spray_area"/>
        <TLCTerm id="term-unauthorised_burning" showAs="unauthorised burning" href="/ontology/term/this.eng.unauthorised_burning"/>
        <TLCTerm id="term-vehicle" showAs="vehicle" href="/ontology/term/this.eng.vehicle"/>
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
      <p>WHEREAS Part B of Schedule 4 of the <ref href="/za/act/1996/constitution">Constitution</ref> lists air pollution as a local government matter to the extent set out in section 155(6)(a) and (7);</p>
      <p>WHEREAS section 156(1)(a) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to administer local government matters listed in Part B of Schedule 4 and Part B of Schedule 5;</p>
      <p>WHEREAS section 156(2) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality may make and administer by-laws for the effective administration of the matters which it has the right to administer;</p>
      <p>WHEREAS section 156(5) of the <ref href="/za/act/1996/constitution">Constitution</ref> provides that a municipality has the right to exercise any power concerning a matter reasonably necessary for, or incidental to, the effective performance of its functions;</p>
      <p>AND WHEREAS the City of Cape Town seeks to ensure management of air quality and the control of air pollution within the area of jurisdiction of the City of Cape Town and to ensure that air pollution is avoided or, where it cannot be altogether avoided, is minimised and remedied.</p>
      <p>AND NOW THEREFORE, BE IT ENACTED by the Council of the City of Cape Town, as follows:-</p>
    </preamble>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <paragraph id="section-1.paragraph0">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Air_Quality_Act">"<def refersTo="#term-Air_Quality_Act">Air Quality Act</def>" means the National Environmental Management: Air Quality Act, 2004 (<ref href="/za/act/2004/39">Act No. 39 of 2004</ref>);</p>
              <p refersTo="#term-adverse_effect">"<def refersTo="#term-adverse_effect">adverse effect</def>" means any actual or potential impact on the <term refersTo="#term-environment" id="trm0">environment</term> that impairs or would impair the <term refersTo="#term-environment" id="trm1">environment</term> or any aspect of it to an extent that is more than trivial or insignificant;</p>
              <p refersTo="#term-air_pollutant">"<def refersTo="#term-air_pollutant">air pollutant</def>" includes any <term refersTo="#term-dust" id="trm2">dust</term>, <term refersTo="#term-smoke" id="trm3">smoke</term>, fumes or gas that causes or may cause <term refersTo="#term-air_pollution" id="trm4">air pollution</term>;</p>
              <p refersTo="#term-air_pollution">"<def refersTo="#term-air_pollution">air pollution</def>" means any change in the <term refersTo="#term-environment" id="trm5">environment</term> caused by any substance emitted into the <term refersTo="#term-atmosphere" id="trm6">atmosphere</term> from any activity, where that change has an <term refersTo="#term-adverse_effect" id="trm7">adverse effect</term> on human health or well-being or on the composition, resilience and productivity of natural or managed ecosystems, or on materials useful to people, or will have such an effect in the future;</p>
              <p refersTo="#term-air_pollution_control_zone">"<def refersTo="#term-air_pollution_control_zone">air pollution control zone</def>" means a geographical area declared in terms of section 8 of the By-Law to be an air pollution control zone for purposes of Chapter IV of the By-Law;</p>
              <p refersTo="#term-air_quality_management_plan">"<def refersTo="#term-air_quality_management_plan">air quality management plan</def>" means the air quality management plan referred to in section 15 of the <term refersTo="#term-Air_Quality_Act" id="trm8">Air Quality Act</term>;</p>
              <p refersTo="#term-air_quality_officer">"<def refersTo="#term-air_quality_officer">air quality officer</def>" means the air quality officer designated as such in terms of section 14(3) of the <term refersTo="#term-Air_Quality_Act" id="trm9">Air Quality Act</term>;</p>
              <p refersTo="#term-ambient_air">"<def refersTo="#term-ambient_air">ambient air</def>" means "ambient air" as defined in section 1 of the <term refersTo="#term-Air_Quality_Act" id="trm10">Air Quality Act</term>;</p>
              <p refersTo="#term-atmosphere">"<def refersTo="#term-atmosphere">atmosphere</def>" means air that is not enclosed by a building, machine, <term refersTo="#term-chimney" id="trm11">chimney</term> or other similar structure;</p>
              <p refersTo="#term-atmospheric_emission">"<def refersTo="#term-atmospheric_emission">atmospheric emission</def>" or "emission" means any emission or entrainment process emanating from a point, non-point or mobile source, as defined in the <term refersTo="#term-Air_Quality_Act" id="trm12">Air Quality Act</term> that results in <term refersTo="#term-air_pollution" id="trm13">air pollution</term>;</p>
              <p refersTo="#term-authorised_official">"<def refersTo="#term-authorised_official">authorised official</def>" means an employee of the <term refersTo="#term-City" id="trm14">City</term> responsible for carrying out any duty or function or exercising any power in terms of this By-law, and includes employees delegated to carry out or exercise such duties, functions or powers;</p>
              <p refersTo="#term-best_practicable_environmental_option">"<def refersTo="#term-best_practicable_environmental_option">best practicable environmental option</def>" means the option that provides the most benefit, or causes the least damage to the <term refersTo="#term-environment" id="trm15">environment</term> as a whole, at a cost acceptable in the long term as well as in the short term;</p>
              <p refersTo="#term-burnt_metal">"<def refersTo="#term-burnt_metal">burnt metal</def>" means any metal that has had its exterior coating removed by means of burning in any place or device other than an approved incineration device, for the purpose of recovering the metal beneath the exterior coating;</p>
              <p refersTo="#term-chimney">"<def refersTo="#term-chimney">chimney</def>" means any structure or opening of any kind from which or through which air pollutants may be emitted;</p>
              <p refersTo="#term-City">"<def refersTo="#term-City">City</def>" means the City of Cape Town established by Provincial Notice No. 479 of 2000 in terms of section 12 of the Local Government: Municipal Structures Act, 1998 (<ref href="/za/act/1998/117">Act No. 117 of 1998</ref>) or any structure or employee of the City acting in terms of delegated authority;</p>
              <p refersTo="#term-City_Manager">"<def refersTo="#term-City_Manager">City Manager</def>" means a <term refersTo="#term-person" id="trm16">person</term> appointed by the <term refersTo="#term-Council" id="trm17">Council</term> in terms of section 54A of the Local Government: <term refersTo="#term-Municipal_Systems_Act" id="trm18">Municipal Systems Act</term>, 2000 (<ref href="/za/act/2000/32">Act No. 32 of 2000</ref>);</p>
              <p refersTo="#term-compression_ignition_powered_vehicle">"<def refersTo="#term-compression_ignition_powered_vehicle">compression ignition powered vehicle</def>" means a <term refersTo="#term-vehicle" id="trm19">vehicle</term> powered by an internal combustion, compression ignition, diesel or similar fuel engine;</p>
              <p refersTo="#term-continuing_offence">"<def refersTo="#term-continuing_offence">continuing offence</def>" means an offence where the act or omission giving rise to the issuing of a notice has not been repaired, removed or rectified by the expiry of a notice issued in terms of this By-law;</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.paragraph0.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.paragraph0.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <p refersTo="#term-directive">"<def refersTo="#term-directive">directive</def>" means an instruction issued by the delegated authority for a <term refersTo="#term-person" id="trm29">person</term> to perform or cease to perform certain activities in order to prevent any detrimental effect on air quality, health or the <term refersTo="#term-environment" id="trm30">environment</term>;</p>
              <p refersTo="#term-dust">"<def refersTo="#term-dust">dust</def>" means any solid matter in a fine or disintegrated form which is capable of being dispersed or suspended in the <term refersTo="#term-atmosphere" id="trm31">atmosphere</term>;</p>
              <p refersTo="#term-dwelling">"<def refersTo="#term-dwelling">dwelling</def>" means any building or structure, or part of a building or structure used as a place of temporary or permanent residence, and includes any outbuilding or other structure ancillary to it;</p>
              <blockList id="section-1.paragraph0.list1" refersTo="#term-environment">
                <listIntroduction>"<def refersTo="#term-environment">environment</def>" means the surroundings within which humans exist and that are made up of-</listIntroduction>
                <item id="section-1.paragraph0.list1.a">
                  <num>(a)</num>
                  <p>the land, water and <term refersTo="#term-atmosphere" id="trm32">atmosphere</term> of the earth;</p>
                </item>
                <item id="section-1.paragraph0.list1.b">
                  <num>(b)</num>
                  <p>micro-organisms, plant and animal life;</p>
                </item>
                <item id="section-1.paragraph0.list1.c">
                  <num>(c)</num>
                  <p>any part or combination of (a) and (b) and the interrelationships among and between them; and</p>
                </item>
                <item id="section-1.paragraph0.list1.d">
                  <num>(d)</num>
                  <p>the physical, chemical, aesthetic and cultural properties and conditions of the foregoing that influence human health and well-being;</p>
                </item>
              </blockList>
              <p refersTo="#term-Executive_Director__City_Health">"<def refersTo="#term-Executive_Director__City_Health">Executive Director: City Health</def>" means the Executive Director of the <term refersTo="#term-City" id="trm33">City</term> responsible for health matters;</p>
              <p refersTo="#term-free_acceleration_test">"<def refersTo="#term-free_acceleration_test">free acceleration test</def>" means the testing procedure described in <ref href="#section-23">section 23</ref>;</p>
              <blockList id="section-1.paragraph0.list2" refersTo="#term-fuel_burning_equipment">
                <listIntroduction>"<def refersTo="#term-fuel_burning_equipment">fuel-burning equipment</def>" means any installed furnace, boiler, burner, incinerator, smoking device, wood-fired oven, commercial wood or charcoal fired braai, barbecue or other equipment including a <term refersTo="#term-chimney" id="trm34">chimney</term>–</listIntroduction>
                <item id="section-1.paragraph0.list2.a">
                  <num>(a)</num>
                  <p>designed to burn or capable of burning liquid, gas or solid fuel;</p>
                </item>
                <item id="section-1.paragraph0.list2.b">
                  <num>(b)</num>
                  <p>used to dispose of any material including general and hazardous waste by the application of heat at a rate of less than 10 kg of waste per day; or</p>
                </item>
                <item id="section-1.paragraph0.list2.c">
                  <num>(c)</num>
                  <p>used to subject liquid, gas or solid fuel to any process involving the application of heat;</p>
                </item>
              </blockList>
              <p>but excludes standby generators and temporary standby generators; domestic <term refersTo="#term-fuel_burning_equipment" id="trm35">fuel-burning equipment</term>; and gas-fired commercial cooking equipment;</p>
              <p refersTo="#term-light_absorption_meter">"<def refersTo="#term-light_absorption_meter">light absorption meter</def>" means a measuring device that uses a light sensitive cell or detector to determine the amount of light absorbed by an <term refersTo="#term-air_pollutant" id="trm36">air pollutant</term>;</p>
              <p refersTo="#term-living_organism">"<def refersTo="#term-living_organism">living organism</def>" means any biological entity capable of transferring or replicating genetic material, including sterile organisms and viruses;</p>
              <p refersTo="#term-Municipal_Systems_Act">"<def refersTo="#term-Municipal_Systems_Act">Municipal Systems Act</def>" means the Local Government: Municipal Systems Act, 2000, (Act No. 32 of);</p>
              <blockList id="section-1.paragraph0.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.paragraph0.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.paragraph0.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
              <p refersTo="#term-obscuration">"<def refersTo="#term-obscuration">obscuration</def>" means the ratio of visible light attenuated by air pollutants suspended in the effluent streams to incident visible light, expressed as a percentage;</p>
              <p refersTo="#term-open_burning">"<def refersTo="#term-open_burning">open burning</def>" means the combustion of any material by burning without a <term refersTo="#term-chimney" id="trm41">chimney</term> to vent the emitted products of combustion to the <term refersTo="#term-atmosphere" id="trm42">atmosphere</term> and includes fires for fire safety training purposes, but excludes any recreational or commercial braai, and "burning in the open" has a corresponding meaning;</p>
              <p refersTo="#term-operator">"<def refersTo="#term-operator">operator</def>" means a <term refersTo="#term-person" id="trm43">person</term> who owns or manages an undertaking, or who controls an operation or process, which emits air pollutants;</p>
              <p refersTo="#term-person">"<def refersTo="#term-person">person</def>" means a natural person or a juristic person;</p>
              <blockList id="section-1.paragraph0.list4" refersTo="#term-premises">
                <listIntroduction>"<def refersTo="#term-premises">premises</def>" includes-</listIntroduction>
                <item id="section-1.paragraph0.list4.a">
                  <num>(a)</num>
                  <p>any building or other structure;</p>
                </item>
                <item id="section-1.paragraph0.list4.b">
                  <num>(b)</num>
                  <p>any adjoining land occupied or used in connection with any activities carried on in that building or structure;</p>
                </item>
                <item id="section-1.paragraph0.list4.c">
                  <num>(c)</num>
                  <p>any vacant land;</p>
                </item>
                <item id="section-1.paragraph0.list4.d">
                  <num>(d)</num>
                  <p>any locomotive, ship, boat or other vessel which operates in the jurisdiction of the <term refersTo="#term-City" id="trm44">City</term> of Cape Town; and</p>
                </item>
                <item id="section-1.paragraph0.list4.e">
                  <num>(e)</num>
                  <p>any State-owned entity or land;</p>
                </item>
              </blockList>
              <p refersTo="#term-Provincial_Government">"<def refersTo="#term-Provincial_Government">Provincial Government</def>" means the Provincial Government of the Western Cape;</p>
              <p refersTo="#term-public_road">"<def refersTo="#term-public_road">public road</def>" means a road which the public has the right to use;</p>
              <p refersTo="#term-smoke">"<def refersTo="#term-smoke">smoke</def>" means the gases, particulate matter and products of combustion emitted into the <term refersTo="#term-atmosphere" id="trm45">atmosphere</term> when material is burned or subjected to heat and includes the soot, grit and gritty particles emitted in smoke;</p>
              <p refersTo="#term-specialist_study">"<def refersTo="#term-specialist_study">specialist study</def>" means any scientifically based study relating to air quality conducted by an expert or recognised specialist of appropriate qualifications and competency in the discipline of air quality management;</p>
              <p refersTo="#term-spray_area">"<def refersTo="#term-spray_area">spray area</def>" means an area or enclosure referred to in <ref href="#section-25">section 25</ref> used for spray painting, and "spray booth" has a corresponding meaning;</p>
              <p refersTo="#term-unauthorised_burning">"<def refersTo="#term-unauthorised_burning">unauthorised burning</def>" means burning of any material in any place or device on any <term refersTo="#term-premises" id="trm46">premises</term> other than in an approved incineration device without obtaining the prior written authorisation of the <term refersTo="#term-City" id="trm47">City</term>; and</p>
              <p refersTo="#term-vehicle">"<def refersTo="#term-vehicle">vehicle</def>" means any motor car, motor cycle, bus, motor lorry or other conveyance propelled wholly or partly by any volatile spirit, steam, gas or oil, or by any means other than human or animal power.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <paragraph id="section-2.paragraph0">
            <content>
              <p>This By-law applies to all properties or <term refersTo="#term-premises" id="trm48">premises</term> within the area of jurisdiction of the <term refersTo="#term-City" id="trm49">City</term> of Cape Town.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-3">
          <num>3.</num>
          <heading>Conflict with other laws</heading>
          <paragraph id="section-3.paragraph0">
            <content>
              <p>In the event of any conflict between this By-law and any other by-law or any policy which regulates <term refersTo="#term-air_pollution" id="trm50">air pollution</term>, the provisions of this By-law shall prevail in so far as it relates to air quality management.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-II">
        <num>II</num>
        <heading>Duty of care</heading>
        <section id="section-4">
          <num>4.</num>
          <heading>Reasonable measures to prevent <term refersTo="#term-air_pollution" id="trm51">air pollution</term></heading>
          <subsection id="section-4.1">
            <num>(1)</num>
            <content>
              <blockList id="section-4.1.list0">
                <listIntroduction>Any <term refersTo="#term-person" id="trm52">person</term> who is wholly or partially responsible for causing <term refersTo="#term-air_pollution" id="trm53">air pollution</term> or creating a risk of <term refersTo="#term-air_pollution" id="trm54">air pollution</term> occurring must take all reasonable measures including the <term refersTo="#term-best_practicable_environmental_option" id="trm55">best practicable environmental option</term>–</listIntroduction>
                <item id="section-4.1.list0.a">
                  <num>(a)</num>
                  <p>to prevent any potential significant <term refersTo="#term-air_pollution" id="trm56">air pollution</term> from occurring; and</p>
                </item>
                <item id="section-4.1.list0.b">
                  <num>(b)</num>
                  <p>to mitigate and, as far as reasonably possible, remedy the environmental impacts and consequences of any <term refersTo="#term-air_pollution" id="trm57">air pollution</term> that has occurred.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-4.2">
            <num>(2)</num>
            <content>
              <blockList id="section-4.2.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm58">City</term> may direct any <term refersTo="#term-person" id="trm59">person</term> who fails to take the measures required under subsection (1) to—</listIntroduction>
                <item id="section-4.2.list0.a">
                  <num>(a)</num>
                  <p>investigate, evaluate and assess the impact on the <term refersTo="#term-environment" id="trm60">environment</term> of specific activities and report thereon;</p>
                </item>
                <item id="section-4.2.list0.b">
                  <num>(b)</num>
                  <p>take specific reasonable measures before a given date;</p>
                </item>
                <item id="section-4.2.list0.c">
                  <num>(c)</num>
                  <p>diligently continue with those measures; and</p>
                </item>
                <item id="section-4.2.list0.d">
                  <num>(d)</num>
                  <p>complete them before a specified reasonable date,</p>
                </item>
              </blockList>
              <p>provided that prior to such direction the <term refersTo="#term-City" id="trm61">City</term> must give such <term refersTo="#term-person" id="trm62">person</term> adequate notice and direct him or her to inform the authorised official of his or her relevant interests.</p>
            </content>
          </subsection>
          <subsection id="section-4.3">
            <num>(3)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm63">City</term> may, if a <term refersTo="#term-person" id="trm64">person</term> fails to comply or inadequately complies with a <term refersTo="#term-directive" id="trm65">directive</term> contemplated in subsection (2), take reasonable measures to remedy the situation.</p>
            </content>
          </subsection>
          <subsection id="section-4.4">
            <num>(4)</num>
            <content>
              <blockList id="section-4.4.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm66">City</term> may, if a <term refersTo="#term-person" id="trm67">person</term> fails to carry out the measures referred to in subsection (1), recover all reasonable costs incurred as a result of it acting under subsection (3) from any or all of the following persons:</listIntroduction>
                <item id="section-4.4.list0.a">
                  <num>(a)</num>
                  <p>any <term refersTo="#term-person" id="trm68">person</term> who is or was responsible for, or who directly or indirectly contributed to the <term refersTo="#term-air_pollution" id="trm69">air pollution</term> or the potential <term refersTo="#term-air_pollution" id="trm70">air pollution</term>;</p>
                </item>
                <item id="section-4.4.list0.b">
                  <num>(b)</num>
                  <p>the owner of the land at the time when the <term refersTo="#term-air_pollution" id="trm71">air pollution</term> or the potential for <term refersTo="#term-air_pollution" id="trm72">air pollution</term> occurred;</p>
                </item>
                <item id="section-4.4.list0.c">
                  <num>(c)</num>
                  <blockList id="section-4.4.list0.c.list0">
                    <listIntroduction>the <term refersTo="#term-person" id="trm73">person</term> in control of the land or any <term refersTo="#term-person" id="trm74">person</term> who has or had a right to use the land at the time when the—</listIntroduction>
                    <item id="section-4.4.list0.c.list0.i">
                      <num>(i)</num>
                      <p>activity or the process in question is or was performed or undertaken; or</p>
                    </item>
                    <item id="section-4.4.list0.c.list0.ii">
                      <num>(ii)</num>
                      <p>situation came about; or</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-4.4.list0.d">
                  <num>(d)</num>
                  <blockList id="section-4.4.list0.d.list0">
                    <listIntroduction>any <term refersTo="#term-person" id="trm75">person</term> who negligently failed to prevent the—</listIntroduction>
                    <item id="section-4.4.list0.d.list0.i">
                      <num>(i)</num>
                      <p>activity or the process being performed or undertaken; or</p>
                    </item>
                    <item id="section-4.4.list0.d.list0.ii">
                      <num>(ii)</num>
                      <p>situation from coming about.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-4.5">
            <num>(5)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm76">person</term> who fails to comply with a <term refersTo="#term-directive" id="trm77">directive</term> referred to in 4(2) commits an offence in terms of Chapter XI of this By-Law.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-III">
        <num>III</num>
        <heading>Designation of the <term refersTo="#term-air_quality_officer" id="trm78">air quality officer</term></heading>
        <section id="section-5">
          <num>5.</num>
          <heading>Designation or appointment of the <term refersTo="#term-air_quality_officer" id="trm79">air quality officer</term></heading>
          <paragraph id="section-5.paragraph0">
            <content>
              <p>The <term refersTo="#term-City_Manager" id="trm80">City Manager</term> must, in consultation with the <term refersTo="#term-Executive_Director__City_Health" id="trm81">Executive Director: City Health</term>, designate or appoint an employee of the <term refersTo="#term-City" id="trm82">City</term> as the Air Quality Officer to be responsible for co-ordinating matters pertaining to air quality management and granting or rejecting Atmospheric Emission Licences or Provisional Atmospheric Emission Licences in terms of the <term refersTo="#term-Air_Quality_Act" id="trm83">Air Quality Act</term> within the <term refersTo="#term-City" id="trm84">City</term>’s jurisdiction.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-IV">
        <num>IV</num>
        <heading>Local emissions standards, norms and standards and <term refersTo="#term-smoke" id="trm85">smoke</term> control zones</heading>
        <part id="chapter-IV.part-1">
          <num>1</num>
          <heading>Local emissions standards</heading>
          <section id="section-6">
            <num>6.</num>
            <heading>Legal mandate</heading>
            <subsection id="section-6.1">
              <num>(1)</num>
              <content>
                <blockList id="section-6.1.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm86">City</term> may, by notice -</listIntroduction>
                  <item id="section-6.1.list0.a">
                    <num>(a)</num>
                    <p>identify substances or mixtures of substances in <term refersTo="#term-ambient_air" id="trm87">ambient air</term> which, through ambient concentrations, bioaccumulation, deposition or in any other way, present a threat to health, well-being or the <term refersTo="#term-environment" id="trm88">environment</term> in the area of jurisdiction of the <term refersTo="#term-City" id="trm89">City</term> of Cape Town or which the <term refersTo="#term-air_quality_officer" id="trm90">air quality officer</term> reasonably believes present such a threat; and</p>
                  </item>
                  <item id="section-6.1.list0.b">
                    <num>(b)</num>
                    <p>in respect of each of those substances or mixtures of substances, publish local standards for emissions from point, non-point or mobile sources in the area of jurisdiction of <term refersTo="#term-City" id="trm91">City</term> of Cape Town.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-6.2">
              <num>(2)</num>
              <content>
                <blockList id="section-6.2.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm92">City</term> may take the following factors into consideration in setting local emission standards:</listIntroduction>
                  <item id="section-6.2.list0.a">
                    <num>(a)</num>
                    <p>health, safety and environmental protection objectives;</p>
                  </item>
                  <item id="section-6.2.list0.b">
                    <num>(b)</num>
                    <p>analytical methodology;</p>
                  </item>
                  <item id="section-6.2.list0.c">
                    <num>(c)</num>
                    <p>technical feasibility;</p>
                  </item>
                  <item id="section-6.2.list0.d">
                    <num>(d)</num>
                    <p>monitoring capability;</p>
                  </item>
                  <item id="section-6.2.list0.e">
                    <num>(e)</num>
                    <p>socio-economic consequences;</p>
                  </item>
                  <item id="section-6.2.list0.f">
                    <num>(f)</num>
                    <p>ecological role of fire in vegetation remnants; and</p>
                  </item>
                  <item id="section-6.2.list0.g">
                    <num>(g)</num>
                    <p><term refersTo="#term-best_practicable_environmental_option" id="trm93">best practicable environmental option</term>.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-6.3">
              <num>(3)</num>
              <content>
                <p>Any <term refersTo="#term-person" id="trm94">person</term> who is emitting substances or mixtures of substances as referred to in subsection (1) must comply with the local emission standards published in terms of this By-law and the failure to do so constitutes an offence in terms of Chapter XI of this By-law.</p>
              </content>
            </subsection>
          </section>
        </part>
        <part id="chapter-IV.part-2">
          <num>2</num>
          <heading>Norms and standards</heading>
          <section id="section-7">
            <num>7.</num>
            <heading>Substances identification process</heading>
            <subsection id="section-7.1">
              <num>(1)</num>
              <content>
                <blockList id="section-7.1.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm95">City</term> must when identifying and prioritising the substances in <term refersTo="#term-ambient_air" id="trm96">ambient air</term> that present a threat to public health, well-being or the <term refersTo="#term-environment" id="trm97">environment</term> consider the following:</listIntroduction>
                  <item id="section-7.1.list0.a">
                    <num>(a)</num>
                    <p>the possibility, severity and frequency of effects with regard to human health and the <term refersTo="#term-environment" id="trm98">environment</term> as a whole, with irreversible effects being of special concern;</p>
                  </item>
                  <item id="section-7.1.list0.b">
                    <num>(b)</num>
                    <p>ubiquitous and high concentrations of the substance in the <term refersTo="#term-atmosphere" id="trm99">atmosphere</term>;</p>
                  </item>
                  <item id="section-7.1.list0.c">
                    <num>(c)</num>
                    <p>potential environmental transformations and metabolic alterations of the substance, as these changes may lead to the production of chemicals with greater toxicity persistence in the <term refersTo="#term-environment" id="trm100">environment</term>, particularly if the substance is not biodegradable and is able to accumulate in humans, the <term refersTo="#term-environment" id="trm101">environment</term> or food chains;</p>
                  </item>
                  <item id="section-7.1.list0.d">
                    <num>(d)</num>
                    <blockList id="section-7.1.list0.d.list0">
                      <listIntroduction>the impact of the substance taking the following factors into consideration:</listIntroduction>
                      <item id="section-7.1.list0.d.list0.i">
                        <num>(i)</num>
                        <p>size of the exposed population, living resources or ecosystems;</p>
                      </item>
                      <item id="section-7.1.list0.d.list0.ii">
                        <num>(ii)</num>
                        <p>the existence of particularly sensitive receptors in the zone concerned; and</p>
                      </item>
                    </blockList>
                  </item>
                  <item id="section-7.1.list0.e">
                    <num>(e)</num>
                    <p>substances that are regulated by international conventions.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-7.2">
              <num>(2)</num>
              <content>
                <p>The <term refersTo="#term-air_quality_officer" id="trm102">air quality officer</term> must, using the criteria set out in subsection (1), compile a list of substances in <term refersTo="#term-ambient_air" id="trm103">ambient air</term> that present a threat to public health, well-being or the <term refersTo="#term-environment" id="trm104">environment</term>.</p>
              </content>
            </subsection>
          </section>
          <section id="section-8">
            <num>8.</num>
            <heading>Declaration of <term refersTo="#term-air_pollution_control_zone" id="trm105">air pollution control zone</term></heading>
            <subsection id="section-8.1">
              <num>(1)</num>
              <content>
                <p>The entire area of the jurisdiction of the <term refersTo="#term-City" id="trm106">City</term> of Cape Town is hereby declared to be an <term refersTo="#term-air_pollution_control_zone" id="trm107">air pollution control zone</term>.</p>
              </content>
            </subsection>
            <subsection id="section-8.2">
              <num>(2)</num>
              <content>
                <blockList id="section-8.2.list0">
                  <listIntroduction>The <term refersTo="#term-City" id="trm108">City</term> may, within the <term refersTo="#term-air_pollution_control_zone" id="trm109">air pollution control zone</term>, from time to time by notice in the Provincial Gazette -</listIntroduction>
                  <item id="section-8.2.list0.a">
                    <num>(a)</num>
                    <p>prohibit or restrict the emission of one or more air pollutants from all <term refersTo="#term-premises" id="trm110">premises</term> or certain <term refersTo="#term-premises" id="trm111">premises</term>;</p>
                  </item>
                  <item id="section-8.2.list0.b">
                    <num>(b)</num>
                    <p>prohibit or restrict the combustion of certain types of fuel;</p>
                  </item>
                  <item id="section-8.2.list0.c">
                    <num>(c)</num>
                    <blockList id="section-8.2.list0.c.list0">
                      <listIntroduction>prescribe different requirements in an <term refersTo="#term-air_pollution_control_zone" id="trm112">air pollution control zone</term> relating to air quality in respect of:</listIntroduction>
                      <item id="section-8.2.list0.c.list0.i">
                        <num>(i)</num>
                        <p>different geographical portions;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.ii">
                        <num>(ii)</num>
                        <p>specified <term refersTo="#term-premises" id="trm113">premises</term>;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.iii">
                        <num>(iii)</num>
                        <p>classes of <term refersTo="#term-premises" id="trm114">premises</term>;</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.iv">
                        <num>(iv)</num>
                        <p><term refersTo="#term-premises" id="trm115">premises</term> used for specified purposes; or</p>
                      </item>
                      <item id="section-8.2.list0.c.list0.v">
                        <num>(v)</num>
                        <p>mobile sources.</p>
                      </item>
                    </blockList>
                  </item>
                </blockList>
              </content>
            </subsection>
            <subsection id="section-8.3">
              <num>(3)</num>
              <content>
                <p>The <term refersTo="#term-City" id="trm116">City</term> may develop and publish policies and guidelines, including technical guidelines, nrelating to the regulation of activities which directly and indirectly cause <term refersTo="#term-air_pollution" id="trm117">air pollution</term> within an <term refersTo="#term-air_pollution_control_zone" id="trm118">air pollution control zone</term>.</p>
              </content>
            </subsection>
            <subsection id="section-8.4">
              <num>(4)</num>
              <content>
                <p>No owner or occupier of any <term refersTo="#term-premises" id="trm119">premises</term> shall cause or permit the emanation or emission of <term refersTo="#term-smoke" id="trm120">smoke</term> of such a density or content from such <term refersTo="#term-premises" id="trm121">premises</term> as will obscure light to an extent greater than twenty (20) per cent.</p>
              </content>
            </subsection>
          </section>
        </part>
      </chapter>
      <chapter id="chapter-V">
        <num>V</num>
        <heading>Smoke emissions from <term refersTo="#term-premises" id="trm122">premises</term> other than dwellings</heading>
        <section id="section-9">
          <num>9.</num>
          <heading>Application</heading>
          <paragraph id="section-9.paragraph0">
            <content>
              <p>For the purposes of this Chapter "<term refersTo="#term-premises" id="trm123">premises</term>" does not include dwellings.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-10">
          <num>10.</num>
          <heading>Prohibition of <term refersTo="#term-dark_smoke" id="trm124">dark smoke</term> from <term refersTo="#term-premises" id="trm125">premises</term></heading>
          <subsection id="section-10.1">
            <num>(1)</num>
            <content>
              <p>Subject to subsection (2), <term refersTo="#term-dark_smoke" id="trm126">dark smoke</term> must not be emitted from any <term refersTo="#term-premises" id="trm127">premises</term> for an aggregate period exceeding three (3) minutes during any continuous period of thirty (30) minutes.</p>
            </content>
          </subsection>
          <subsection id="section-10.2">
            <num>(2)</num>
            <content>
              <p>This section does not apply to <term refersTo="#term-dark_smoke" id="trm128">dark smoke</term> which is emitted from <term refersTo="#term-fuel_burning_equipment" id="trm129">fuel-burning equipment</term> while such equipment is being started, overhauled or repaired, unless such emission could have been prevented using the best practical environmental option.</p>
            </content>
          </subsection>
          <subsection id="section-10.3">
            <num>(3)</num>
            <content>
              <p>Subsections (1) and (2) do not apply to holders of <term refersTo="#term-atmospheric_emission" id="trm130">atmospheric emission</term> licences for activities listed in terms of section 21 of the <term refersTo="#term-Air_Quality_Act" id="trm131">Air Quality Act</term>, and the emission standards listed in such <term refersTo="#term-atmospheric_emission" id="trm132">atmospheric emission</term> licences shall apply.</p>
            </content>
          </subsection>
        </section>
        <section id="section-11">
          <num>11.</num>
          <heading>Installation of <term refersTo="#term-fuel_burning_equipment" id="trm133">fuel-burning equipment</term></heading>
          <subsection id="section-11.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm134">person</term> shall install, alter, extend, replace or operate any <term refersTo="#term-fuel_burning_equipment" id="trm135">fuel-burning equipment</term> on any <term refersTo="#term-premises" id="trm136">premises</term> without the prior written authorisation of the <term refersTo="#term-City" id="trm137">City</term>, which may only be given after consideration of the completed prescribed application form together with the relevant plans and specifications.</p>
            </content>
          </subsection>
          <subsection id="section-11.2">
            <num>(2)</num>
            <content>
              <p>No rights accrue to any <term refersTo="#term-person" id="trm138">person</term> who has applied for written authorisation in terms of subsection (1) during the interim period whilst the application is under consideration.</p>
            </content>
          </subsection>
          <subsection id="section-11.3">
            <num>(3)</num>
            <content>
              <p>A written authorisation granted by the <term refersTo="#term-City" id="trm139">City</term> in respect of the installation, alteration, extension, replacement or operation of any <term refersTo="#term-fuel_burning_equipment" id="trm140">fuel-burning equipment</term> in terms of a by-law concerned with air quality management or a regulation in terms of the Atmospheric Pollution Prevention Act, which has been repealed shall be deemed to satisfy the requirements of subsection (1) where proof of such authorisation is presented to the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-11.4">
            <num>(4)</num>
            <content>
              <blockList id="section-11.4.list0">
                <listIntroduction>Where <term refersTo="#term-fuel_burning_equipment" id="trm141">fuel-burning equipment</term> has been installed, altered, extended or replaced on <term refersTo="#term-premises" id="trm142">premises</term> contrary to subsection (1), the authorised official may, on written notice to the owner of the <term refersTo="#term-premises" id="trm143">premises</term> or to the <term refersTo="#term-operator" id="trm144">operator</term> of the appliance:</listIntroduction>
                <item id="section-11.4.list0.a">
                  <num>(a)</num>
                  <p>order the removal of the <term refersTo="#term-fuel_burning_equipment" id="trm145">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm146">premises</term>, at the expense of the owner, <term refersTo="#term-operator" id="trm147">operator</term> or both within the period stated in the notice, or,</p>
                </item>
                <item id="section-11.4.list0.b">
                  <num>(b)</num>
                  <p>impose a fine not exceeding R10 000 before considering an application for written authorisation in terms of subsection (1).</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-11.5">
            <num>(5)</num>
            <content>
              <p>When ownership of <term refersTo="#term-fuel_burning_equipment" id="trm148">fuel-burning equipment</term> which has been approved by the <term refersTo="#term-City" id="trm149">City</term> is transferred to a new owner, the new owner must apply for written authorisation to use such equipment in terms of subsection (1).</p>
            </content>
          </subsection>
          <subsection id="section-11.6">
            <num>(6)</num>
            <content>
              <p>Fuel-burning equipment must comply with the emission standards as contained in Schedule 1 of this By-law.</p>
            </content>
          </subsection>
        </section>
        <section id="section-12">
          <num>12.</num>
          <heading>Operation of <term refersTo="#term-fuel_burning_equipment" id="trm150">fuel-burning equipment</term></heading>
          <subsection id="section-12.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm151">person</term> may use or operate any <term refersTo="#term-fuel_burning_equipment" id="trm152">fuel-burning equipment</term> on any <term refersTo="#term-premises" id="trm153">premises</term> contrary to a written authorisation referred to in <ref href="#section-11">section 11</ref>(1).</p>
            </content>
          </subsection>
          <subsection id="section-12.2">
            <num>(2)</num>
            <content>
              <blockList id="section-12.2.list0">
                <listIntroduction>Where <term refersTo="#term-fuel_burning_equipment" id="trm154">fuel-burning equipment</term> has been used or operated on a <term refersTo="#term-premises" id="trm155">premises</term> contrary to subsection (1), the authorised official may on written notice to the owner of the <term refersTo="#term-premises" id="trm156">premises</term> or <term refersTo="#term-operator" id="trm157">operator</term> of the <term refersTo="#term-fuel_burning_equipment" id="trm158">fuel-burning equipment</term> -</listIntroduction>
                <item id="section-12.2.list0.a">
                  <num>(a)</num>
                  <p>revoke the written authorisation referred to in subsection (1); and</p>
                </item>
                <item id="section-12.2.list0.b">
                  <num>(b)</num>
                  <p>order the removal of the <term refersTo="#term-fuel_burning_equipment" id="trm159">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm160">premises</term> at the expense of the owner and <term refersTo="#term-operator" id="trm161">operator</term> within the period stated in the notice.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-12.3">
            <num>(3)</num>
            <content>
              <p>In the event that the owner of the <term refersTo="#term-premises" id="trm162">premises</term> or <term refersTo="#term-operator" id="trm163">operator</term> of the <term refersTo="#term-fuel_burning_equipment" id="trm164">fuel-burning equipment</term> fails to comply with a notice issued in terms of subsection (2), the authorised official may remove the <term refersTo="#term-fuel_burning_equipment" id="trm165">fuel-burning equipment</term> from the <term refersTo="#term-premises" id="trm166">premises</term>, and recover the reasonable costs incurred from the owner or <term refersTo="#term-operator" id="trm167">operator</term> in question.</p>
            </content>
          </subsection>
        </section>
        <section id="section-13">
          <num>13.</num>
          <heading>Periodic Emissions Testing</heading>
          <paragraph id="section-13.paragraph0">
            <content>
              <p>The <term refersTo="#term-authorised_official" id="trm168">authorised official</term> may order the owner of the <term refersTo="#term-premises" id="trm169">premises</term> or <term refersTo="#term-operator" id="trm170">operator</term> of any <term refersTo="#term-fuel_burning_equipment" id="trm171">fuel-burning equipment</term> capable of burning solid fuels to conduct periodic emissions testing in accordance with the methods prescribed in Schedule 1 of this By-law.</p>
            </content>
          </paragraph>
        </section>
        <section id="section-14">
          <num>14.</num>
          <heading>Presumption</heading>
          <subsection id="section-14.1">
            <num>(1)</num>
            <content>
              <p>Dark <term refersTo="#term-smoke" id="trm172">smoke</term> shall be presumed to have been emitted from a <term refersTo="#term-premises" id="trm173">premises</term> if it is shown that any fuel or material was burned on the <term refersTo="#term-premises" id="trm174">premises</term>, and that the circumstances were such that the burning was reasonably likely to give rise to the emission of <term refersTo="#term-dark_smoke" id="trm175">dark smoke</term>, unless the owner, occupier or <term refersTo="#term-operator" id="trm176">operator</term>, as the case may be, can show that no <term refersTo="#term-dark_smoke" id="trm177">dark smoke</term> was emitted.</p>
            </content>
          </subsection>
          <subsection id="section-14.2">
            <num>(2)</num>
            <content>
              <p>Where an <term refersTo="#term-authorised_official" id="trm178">authorised official</term> has observed <term refersTo="#term-fuel_burning_equipment" id="trm179">fuel-burning equipment</term> emitting particulate emissions; or <term refersTo="#term-dark_smoke" id="trm180">dark smoke</term> for a period of greater than 3 minutes in every aggregate half hour, the authorised official may issue a compliance notice ordering the <term refersTo="#term-operator" id="trm181">operator</term> or owner to immediately cease the operation of the <term refersTo="#term-fuel_burning_equipment" id="trm182">fuel-burning equipment</term> until such time that the <term refersTo="#term-fuel_burning_equipment" id="trm183">fuel-burning equipment</term> has been repaired to the satisfaction of the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-14.3">
            <num>(3)</num>
            <content>
              <p>Failure to comply with an order issued in terms of subsection (2) shall constitute an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-15">
          <num>15.</num>
          <heading>Installation and operation of <term refersTo="#term-obscuration" id="trm184">obscuration</term> measuring equipment</heading>
          <subsection id="section-15.1">
            <num>(1)</num>
            <content>
              <blockList id="section-15.1.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm185">authorised official</term> may give notice to any <term refersTo="#term-operator" id="trm186">operator</term> of <term refersTo="#term-fuel_burning_equipment" id="trm187">fuel-burning equipment</term>, or any owner or occupier of <term refersTo="#term-premises" id="trm188">premises</term> on which <term refersTo="#term-fuel_burning_equipment" id="trm189">fuel-burning equipment</term> is used or operated, or intended to be used or operated, to install, maintain and operate <term refersTo="#term-obscuration" id="trm190">obscuration</term> measuring equipment at his or her own cost, if -</listIntroduction>
                <item id="section-15.1.list0.a">
                  <num>(a)</num>
                  <p>unauthorised and unlawful emissions of <term refersTo="#term-dark_smoke" id="trm191">dark smoke</term> from the <term refersTo="#term-premises" id="trm192">premises</term> in question have occurred consistently and regularly over a period of at least two days;</p>
                </item>
                <item id="section-15.1.list0.b">
                  <num>(b)</num>
                  <p>unauthorised and unlawful emissions of <term refersTo="#term-dark_smoke" id="trm193">dark smoke</term> from the relevant <term refersTo="#term-premises" id="trm194">premises</term> have occurred intermittently over a period of at least fourteen days;</p>
                </item>
                <item id="section-15.1.list0.c">
                  <num>(c)</num>
                  <p><term refersTo="#term-fuel_burning_equipment" id="trm195">fuel-burning equipment</term> has been, or is intended to be, installed on the <term refersTo="#term-premises" id="trm196">premises</term> in question which is reasonably likely to emit <term refersTo="#term-dark_smoke" id="trm197">dark smoke</term>;</p>
                </item>
                <item id="section-15.1.list0.d">
                  <num>(d)</num>
                  <p>the <term refersTo="#term-person" id="trm198">person</term> on whom the notice is served has been convicted or paid an admission of guilt fine on more than one occasion in the preceding two years for a contravention committed under this Chapter or any previous by-law dealing with air quality matters and has not taken adequate measures to prevent further contravention of the provisions of this Chapter; or</p>
                </item>
                <item id="section-15.1.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm199">authorised official</term> considers that the nature of the air pollutants emitted from the relevant <term refersTo="#term-premises" id="trm200">premises</term> is reasonably likely to pose a risk to human health or the <term refersTo="#term-environment" id="trm201">environment</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-16">
          <num>16.</num>
          <heading>Monitoring and sampling</heading>
          <paragraph id="section-16.paragraph0">
            <content>
              <blockList id="section-16.paragraph0.list0">
                <listIntroduction>An occupier or owner of <term refersTo="#term-premises" id="trm202">premises</term>, and the <term refersTo="#term-operator" id="trm203">operator</term> of any <term refersTo="#term-fuel_burning_equipment" id="trm204">fuel-burning equipment</term>, who is required to install <term refersTo="#term-obscuration" id="trm205">obscuration</term> measuring equipment in terms of <ref href="#section-15">section 15</ref>(1) must -</listIntroduction>
                <item id="section-16.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>record all monitoring and sampling results and maintain a copy of this record for at least four years after obtaining the results;</p>
                </item>
                <item id="section-16.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-16.paragraph0.list0.b.list0">
                    <listIntroduction>if requested to do so by an <term refersTo="#term-authorised_official" id="trm206">authorised official</term> -</listIntroduction>
                    <item id="section-16.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p>produce the record of the monitoring and sampling results for inspection; and</p>
                    </item>
                    <item id="section-16.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p>provide a written report, in a form and by a date specified by the <term refersTo="#term-authorised_official" id="trm207">authorised official</term>, of part or all of the information in the record of the monitoring and sampling results.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </paragraph>
        </section>
        <section id="section-17">
          <num>17.</num>
          <heading>Temporary exemption</heading>
          <subsection id="section-17.1">
            <num>(1)</num>
            <content>
              <p>Subject to <ref href="#section-31">section 31</ref> and upon receipt of a fully motivated application in writing by the owner or occupier of premises or the operator of fuel-burning equipment, the City may grant a temporary exemption in writing from one or all the provisions of this Chapter.</p>
            </content>
          </subsection>
          <subsection id="section-17.2">
            <num>(2)</num>
            <content>
              <blockList id="section-17.2.list0">
                <listIntroduction>Any exemption granted under subsection (1) must state at least the following:</listIntroduction>
                <item id="section-17.2.list0.a">
                  <num>(a)</num>
                  <p>a description of the <term refersTo="#term-fuel_burning_equipment" id="trm208">fuel-burning equipment</term> and the <term refersTo="#term-premises" id="trm209">premises</term> on which it is used or operated;</p>
                </item>
                <item id="section-17.2.list0.b">
                  <num>(b)</num>
                  <p>the reasons for granting the exemption;</p>
                </item>
                <item id="section-17.2.list0.c">
                  <num>(c)</num>
                  <p>the conditions attached to the exemption, if any;</p>
                </item>
                <item id="section-17.2.list0.d">
                  <num>(d)</num>
                  <p>the period for which the exemption has been granted; and</p>
                </item>
                <item id="section-17.2.list0.e">
                  <num>(e)</num>
                  <p>any other relevant information.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-17.3">
            <num>(3)</num>
            <content>
              <blockList id="section-17.3.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm210">City</term> may not grant a temporary exemption under subsection (1) until it has:</listIntroduction>
                <item id="section-17.3.list0.a">
                  <num>(a)</num>
                  <p>taken reasonable measures to ensure that all persons whose rights may be detrimentally affected by the granting of the temporary exemption, including adjacent land owners or occupiers, are aware of the application for temporary exemption and how to obtain a copy of it;</p>
                </item>
                <item id="section-17.3.list0.b">
                  <num>(b)</num>
                  <p>provided such persons with a reasonable opportunity to object to the application; and</p>
                </item>
                <item id="section-17.3.list0.c">
                  <num>(c)</num>
                  <p>duly considered and taken into account any objections raised.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VI">
        <num>VI</num>
        <heading>Smoke emissions from dwellings</heading>
        <section id="section-18">
          <num>18.</num>
          <heading>Prohibition of emission of <term refersTo="#term-dark_smoke" id="trm211">dark smoke</term> from dwellings</heading>
          <subsection id="section-18.1">
            <num>(1)</num>
            <content>
              <p>Subject to <ref href="#section-4">section 4</ref>(1), no person shall emit or permit the emission of dark smoke from any dwelling for an aggregate period exceeding three minutes during any continuous period of thirty minutes.</p>
            </content>
          </subsection>
          <subsection id="section-18.2">
            <num>(2)</num>
            <content>
              <p>Subject to <ref href="#section-31">section 31</ref>, and on application in writing by the owner or occupier of any dwelling, the City may grant a temporary exemption in writing from one or all of the provisions of this Chapter.</p>
            </content>
          </subsection>
          <subsection id="section-18.3">
            <num>(3)</num>
            <content>
              <p>Subject to <ref href="#section-4">section 4</ref>(1), no person shall emit or permit the emission of dark smoke so as to cause a nuisance.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VII">
        <num>VII</num>
        <heading>Emissions caused by <term refersTo="#term-open_burning" id="trm212">open burning</term></heading>
        <section id="section-19">
          <num>19.</num>
          <heading>Authorisation of <term refersTo="#term-open_burning" id="trm213">open burning</term> and burning of material</heading>
          <subsection id="section-19.1">
            <num>(1)</num>
            <content>
              <p>Subject to subsection (4), no <term refersTo="#term-person" id="trm214">person</term> may carry out <term refersTo="#term-open_burning" id="trm215">open burning</term> of any material on any land or <term refersTo="#term-premises" id="trm216">premises</term>, unless such <term refersTo="#term-person" id="trm217">person</term> has first obtained written authorisation for <term refersTo="#term-open_burning" id="trm218">open burning</term> from the <term refersTo="#term-City" id="trm219">City</term>.</p>
            </content>
          </subsection>
          <subsection id="section-19.2">
            <num>(2)</num>
            <content>
              <blockList id="section-19.2.list0">
                <item id="section-19.2.list0.a">
                  <num>(a)</num>
                  <p>Where a third party wishes to conduct <term refersTo="#term-open_burning" id="trm220">open burning</term> on behalf of the owner of a property, written permission must be obtained by the third party from the owner prior to making application to the <term refersTo="#term-City" id="trm221">City</term> for authorisation to conduct <term refersTo="#term-open_burning" id="trm222">open burning</term>.</p>
                </item>
                <item id="section-19.2.list0.b">
                  <num>(b)</num>
                  <p>The <term refersTo="#term-City" id="trm223">City</term> may undertake <term refersTo="#term-open_burning" id="trm224">open burning</term> where it is reasonably necessary and where the owner or occupier cannot be contacted.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.3">
            <num>(3)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm225">City</term> may, in the written authorisation referred to in subsection (1) impose conditions with which the <term refersTo="#term-person" id="trm226">person</term> requesting written authorisation must comply.</p>
            </content>
          </subsection>
          <subsection id="section-19.4">
            <num>(4)</num>
            <content>
              <blockList id="section-19.4.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm227">City</term> may not authorise <term refersTo="#term-open_burning" id="trm228">open burning</term> referred to in subsection (1) unless it is satisfied that the applicant has adequately addressed or fulfilled the following requirements:</listIntroduction>
                <item id="section-19.4.list0.a">
                  <num>(a)</num>
                  <p>the material will be open burned on the land from which it originated;</p>
                </item>
                <item id="section-19.4.list0.b">
                  <num>(b)</num>
                  <p>the <term refersTo="#term-person" id="trm229">person</term> requesting authorisation has investigated and assessed every reasonable alternative for reducing, reusing , recycling or removing the material in order to minimize the amount of material to be open burned, to the satisfaction of the <term refersTo="#term-City" id="trm230">City</term>;</p>
                </item>
                <item id="section-19.4.list0.c">
                  <num>(c)</num>
                  <p>the <term refersTo="#term-person" id="trm231">person</term> requesting authorisation has investigated and assessed the impact the <term refersTo="#term-open_burning" id="trm232">open burning</term> will have on the <term refersTo="#term-environment" id="trm233">environment</term> to the satisfaction of the <term refersTo="#term-City" id="trm234">City</term>;</p>
                </item>
                <item id="section-19.4.list0.d">
                  <num>(d)</num>
                  <blockList id="section-19.4.list0.d.list0">
                    <listIntroduction>the <term refersTo="#term-person" id="trm235">person</term> requesting authorisation has either placed a notice in a local newspaper circulating in the area or notified in writing the owners and or occupiers of all adjacent properties of –</listIntroduction>
                    <item id="section-19.4.list0.d.list0.i">
                      <num>(i)</num>
                      <p>all known details of the proposed <term refersTo="#term-open_burning" id="trm236">open burning</term>; and</p>
                    </item>
                    <item id="section-19.4.list0.d.list0.ii">
                      <num>(ii)</num>
                      <p>the right of owners and occupiers of adjacent properties to lodge written objections to the proposed <term refersTo="#term-open_burning" id="trm237">open burning</term> with the <term refersTo="#term-City" id="trm238">City</term> within seven days of being notified;</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-19.4.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-person" id="trm239">person</term> requesting authorisation has provided proof that the written notification was received by the owners and or occupiers of all adjacent properties at least seven (7) days prior to the <term refersTo="#term-open_burning" id="trm240">open burning</term> application being considered;</p>
                </item>
                <item id="section-19.4.list0.f">
                  <num>(f)</num>
                  <p>the prescribed fee has been paid to the <term refersTo="#term-City" id="trm241">City</term>;</p>
                </item>
                <item id="section-19.4.list0.g">
                  <num>(g)</num>
                  <p>the land on which that <term refersTo="#term-person" id="trm242">person</term> intends to open burn the material is state land, a farm or small-holding, or land within a proclaimed township that is not utilised for residential purposes;</p>
                </item>
                <item id="section-19.4.list0.h">
                  <num>(h)</num>
                  <p>the <term refersTo="#term-open_burning" id="trm243">open burning</term> is conducted at least 100 metres from any buildings or structures; and</p>
                </item>
                <item id="section-19.4.list0.i">
                  <num>(i)</num>
                  <p>the <term refersTo="#term-open_burning" id="trm244">open burning</term> will not pose a potential hazard to human health or safety, private property or to the <term refersTo="#term-environment" id="trm245">environment</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.5">
            <num>(5)</num>
            <content>
              <blockList id="section-19.5.list0">
                <listIntroduction>The provisions of this section shall not apply to -</listIntroduction>
                <item id="section-19.5.list0.a">
                  <num>(a)</num>
                  <p>recreational outdoor barbecue or braai activities on private <term refersTo="#term-premises" id="trm246">premises</term> or in designated spaces;</p>
                </item>
                <item id="section-19.5.list0.b">
                  <num>(b)</num>
                  <p>small controlled fires in informal settlements for the purposes of cooking, heating water and other domestic purposes;</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-19.6">
            <num>(6)</num>
            <content>
              <p>For the purposes of fire safety training sections (4)(a), (b), (f) and (g) shall not apply.</p>
            </content>
          </subsection>
          <subsection id="section-19.7">
            <num>(7)</num>
            <content>
              <p>The management practices set out in schedule 2 to the By-law must be applied to prevent or minimise the discharge of <term refersTo="#term-smoke" id="trm247">smoke</term> from <term refersTo="#term-open_burning" id="trm248">open burning</term> of vegetation within the <term refersTo="#term-City" id="trm249">City</term>’s jurisdiction.</p>
            </content>
          </subsection>
        </section>
        <section id="section-20">
          <num>20.</num>
          <heading>Emissions caused by tyre burning and burning of rubber and other material for the recovery of metal</heading>
          <subsection id="section-20.1">
            <num>(1)</num>
            <content>
              <blockList id="section-20.1.list0">
                <listIntroduction>No <term refersTo="#term-person" id="trm250">person</term> may, without prior written authorisation by the <term refersTo="#term-City" id="trm251">City</term>, on any <term refersTo="#term-premises" id="trm252">premises</term> –</listIntroduction>
                <item id="section-20.1.list0.a">
                  <num>(a)</num>
                  <blockList id="section-20.1.list0.a.list0">
                    <listIntroduction>carry out or permit the burning of any tyres, rubber products, cables, synthetically covered or insulated products, equipment or any other similar product for purposes of</listIntroduction>
                    <item id="section-20.1.list0.a.list0.i">
                      <num>(i)</num>
                      <p>recovering the metal contained therein;</p>
                    </item>
                    <item id="section-20.1.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>disposing of tyres or any other product described in (a) above as waste; or</p>
                    </item>
                    <item id="section-20.1.list0.a.list0.iii">
                      <num>(iii)</num>
                      <p>for any other reason, except for the thermal treatment of general and hazardous waste in any device licensed in terms of section 41(1)(a) of the National Environmental Management: <term refersTo="#term-Air_Quality_Act" id="trm253">Air Quality Act</term>;</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-20.1.list0.b">
                  <num>(b)</num>
                  <p>possess, store, transport or trade in any <term refersTo="#term-burnt_metal" id="trm254">burnt metal</term> recovered as a result of <term refersTo="#term-unauthorised_burning" id="trm255">unauthorised burning</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-20.2">
            <num>(2)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm256">authorised official</term> may for the purpose of gathering evidence, seize any <term refersTo="#term-burnt_metal" id="trm257">burnt metal</term> or metal in the process of being burnt where authorisation in terms of <ref href="#section-20">section 20</ref>(1) has not been obtained or cannot be provided by a person referred to in that subsection.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-VIII">
        <num>VIII</num>
        <heading>Emissions from compression ignition powered vehicles</heading>
        <section id="section-21">
          <num>21.</num>
          <heading>Prohibition of <term refersTo="#term-dark_smoke" id="trm258">dark smoke</term> from compression ignition powered vehicles</heading>
          <subsection id="section-21.1">
            <num>(1)</num>
            <content>
              <p>No <term refersTo="#term-person" id="trm259">person</term> may on a public or private road or any <term refersTo="#term-premises" id="trm260">premises</term> drive or use, or cause to be used, a <term refersTo="#term-compression_ignition_powered_vehicle" id="trm261">compression ignition powered vehicle</term> that emits <term refersTo="#term-dark_smoke" id="trm262">dark smoke</term>.</p>
            </content>
          </subsection>
          <subsection id="section-21.2">
            <num>(2)</num>
            <content>
              <p>For purposes of this Chapter the registered owner of the <term refersTo="#term-vehicle" id="trm263">vehicle</term> shall be presumed to be the driver unless the contrary is proven.</p>
            </content>
          </subsection>
        </section>
        <section id="section-22">
          <num>22.</num>
          <heading>Stopping of vehicles for inspection and testing</heading>
          <subsection id="section-22.1">
            <num>(1)</num>
            <content>
              <p>In order to enable an <term refersTo="#term-authorised_official" id="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" id="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" id="trm266">vehicle</term>.</p>
            </content>
          </subsection>
          <subsection id="section-22.2">
            <num>(2)</num>
            <content>
              <blockList id="section-22.2.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" id="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" id="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" id="trm270">vehicle</term> in order to -</listIntroduction>
                <item id="section-22.2.list0.a">
                  <num>(a)</num>
                  <blockList id="section-22.2.list0.a.list0">
                    <listIntroduction>inspect and test the <term refersTo="#term-vehicle" id="trm271">vehicle</term> at the roadside, in which case inspection and testing must be carried out -</listIntroduction>
                    <item id="section-22.2.list0.a.list0.i">
                      <num>(i)</num>
                      <p>at or as near as practicable to the place where the direction to stop the <term refersTo="#term-vehicle" id="trm272">vehicle</term> is given; and</p>
                    </item>
                    <item id="section-22.2.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>as soon as practicable, and in any case within one hour, after the <term refersTo="#term-vehicle" id="trm273">vehicle</term> is stopped in accordance with the direction; or</p>
                    </item>
                  </blockList>
                </item>
                <item id="section-22.2.list0.b">
                  <num>(b)</num>
                  <p>conduct a visual inspection of the <term refersTo="#term-vehicle" id="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#section-21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#section-23">section 23</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-23">
          <num>23.</num>
          <heading>Testing procedure</heading>
          <subsection id="section-23.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" id="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" id="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#section-21">section 21</ref>(1).</p>
            </content>
          </subsection>
          <subsection id="section-23.2">
            <num>(2)</num>
            <content>
              <blockList id="section-23.2.list0">
                <listIntroduction>The following procedure must be adhered to in order to conduct a <term refersTo="#term-free_acceleration_test" id="trm278">free acceleration test</term>:</listIntroduction>
                <item id="section-23.2.list0.a">
                  <num>(a)</num>
                  <p>when instructed to do so by the <term refersTo="#term-authorised_official" id="trm279">authorised official</term>, the driver must start the <term refersTo="#term-vehicle" id="trm280">vehicle</term>, place it in neutral gear and engage the clutch;</p>
                </item>
                <item id="section-23.2.list0.b">
                  <num>(b)</num>
                  <p>while the <term refersTo="#term-vehicle" id="trm281">vehicle</term> is idling, the <term refersTo="#term-authorised_official" id="trm282">authorised official</term> must conduct a visual inspection of the emission system of the <term refersTo="#term-vehicle" id="trm283">vehicle</term>;</p>
                </item>
                <item id="section-23.2.list0.c">
                  <num>(c)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm284">authorised official</term> must rapidly, smoothly and completely depress the accelerator throttle pedal of the <term refersTo="#term-vehicle" id="trm285">vehicle</term>, or he may instruct the driver to do likewise under his supervision;</p>
                </item>
                <item id="section-23.2.list0.d">
                  <num>(d)</num>
                  <p>while the throttle pedal is depressed, the <term refersTo="#term-authorised_official" id="trm286">authorised official</term> must measure the <term refersTo="#term-smoke" id="trm287">smoke</term> emitted from the emission system of the <term refersTo="#term-vehicle" id="trm288">vehicle</term> in order to determine whether or not it is <term refersTo="#term-dark_smoke" id="trm289">dark smoke</term>;</p>
                </item>
                <item id="section-23.2.list0.e">
                  <num>(e)</num>
                  <p>the <term refersTo="#term-authorised_official" id="trm290">authorised official</term> must release the throttle pedal when the engine reaches cut-off speed;</p>
                </item>
                <item id="section-23.2.list0.f">
                  <num>(f)</num>
                  <p>if the <term refersTo="#term-authorised_official" id="trm291">authorised official</term> instructs the driver to depress the throttle, the driver may only release the throttle when it reaches cut-off speed or when instructed to do so by the <term refersTo="#term-authorised_official" id="trm292">authorised official</term>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-23.3">
            <num>(3)</num>
            <content>
              <blockList id="section-23.3.list0">
                <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" id="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" id="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" id="trm295">vehicle</term> -</listIntroduction>
                <item id="section-23.3.list0.a">
                  <num>(a)</num>
                  <p>is not emitting <term refersTo="#term-dark_smoke" id="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" id="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" id="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#section-21">section 21</ref>; or</p>
                </item>
                <item id="section-23.3.list0.b">
                  <num>(b)</num>
                  <p>is emitting <term refersTo="#term-dark_smoke" id="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" id="trm300">vehicle</term> with a repair notice in accordance with <ref href="#section-24">section 24</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-24">
          <num>24.</num>
          <heading>Repair notice</heading>
          <subsection id="section-24.1">
            <num>(1)</num>
            <content>
              <p>In the event that a determination is made in terms of <ref href="#section-23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
            </content>
          </subsection>
          <subsection id="section-24.2">
            <num>(2)</num>
            <content>
              <p>A copy of the test results must be provided by the registered owner of the <term refersTo="#term-vehicle" id="trm301">vehicle</term> or his representative to the authorised official where the testing station is not a <term refersTo="#term-City" id="trm302">City</term> testing facility on or before the due date of the repair notice.</p>
            </content>
          </subsection>
          <subsection id="section-24.3">
            <num>(3)</num>
            <content>
              <blockList id="section-24.3.list0">
                <listIntroduction>The repair notice must contain the following information:</listIntroduction>
                <item id="section-24.3.list0.a">
                  <num>(a)</num>
                  <p>the make and registration number of the <term refersTo="#term-vehicle" id="trm303">vehicle</term>;</p>
                </item>
                <item id="section-24.3.list0.b">
                  <num>(b)</num>
                  <p>the name, address and identity number of the driver of the <term refersTo="#term-vehicle" id="trm304">vehicle</term>; and</p>
                </item>
                <item id="section-24.3.list0.c">
                  <num>(c)</num>
                  <p>if the driver is not the owner of the <term refersTo="#term-vehicle" id="trm305">vehicle</term>, the name and address of the <term refersTo="#term-vehicle" id="trm306">vehicle</term> owner.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-24.4">
            <num>(4)</num>
            <content>
              <p>The owner of a <term refersTo="#term-vehicle" id="trm307">vehicle</term> is deemed to have been notified of the repair notice on the date that such notice is issued.</p>
            </content>
          </subsection>
          <subsection id="section-24.5">
            <num>(5)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm308">City</term> may take whatever steps it considers necessary in the event that the requirements of subsection (1) are not complied with, including impounding the <term refersTo="#term-vehicle" id="trm309">vehicle</term> and recovering any costs incurred in that regard from the owner of the <term refersTo="#term-vehicle" id="trm310">vehicle</term>.</p>
            </content>
          </subsection>
        </section>
      </chapter>
      <chapter id="chapter-IX">
        <num>IX</num>
        <heading>Emissions that cause a <term refersTo="#term-nuisance" id="trm311">nuisance</term></heading>
        <section id="section-25">
          <num>25.</num>
          <heading>Prohibition of emissions that cause <term refersTo="#term-nuisance" id="trm312">nuisance</term></heading>
          <subsection id="section-25.1">
            <num>(1)</num>
            <content>
              <blockList id="section-25.1.list0">
                <listIntroduction>No <term refersTo="#term-person" id="trm313">person</term> shall, within the area of jurisdiction of the <term refersTo="#term-City" id="trm314">City</term> of Cape Town-</listIntroduction>
                <item id="section-25.1.list0.a">
                  <num>(a)</num>
                  <p>spray or apply any coat, plate or epoxy coat to any <term refersTo="#term-vehicle" id="trm315">vehicle</term>, article or object, inside an approved <term refersTo="#term-spray_area" id="trm316">spray area</term> or spray booth, so as to cause a <term refersTo="#term-nuisance" id="trm317">nuisance</term>; or</p>
                </item>
                <item id="section-25.1.list0.b">
                  <num>(b)</num>
                  <p>spray, coat, plate or epoxy coat to be applied to any such <term refersTo="#term-vehicle" id="trm318">vehicle</term>, article or object or allow it to be sprayed, coated plated or epoxy coated or similar activity outside an approved <term refersTo="#term-spray_area" id="trm319">spray area</term> or spray booth.</p>
                </item>
                <item id="section-25.1.list0.c">
                  <num>(c)</num>
                  <blockList id="section-25.1.list0.c.list0">
                    <listIntroduction>cause any unreasonable interference or likely interference through <term refersTo="#term-air_pollution" id="trm320">air pollution</term>, which may adversely affect -</listIntroduction>
                    <item id="section-25.1.list0.c.list0.i">
                      <num>(i)</num>
                      <p>the health or well-being of any <term refersTo="#term-person" id="trm321">person</term> or <term refersTo="#term-living_organism" id="trm322">living organism</term>; or</p>
                    </item>
                    <item id="section-25.1.list0.c.list0.ii">
                      <num>(ii)</num>
                      <p>the use and enjoyment by an owner or occupier of his or her property or <term refersTo="#term-environment" id="trm323">environment</term>;</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.2">
            <num>(2)</num>
            <content>
              <blockList id="section-25.2.list0">
                <listIntroduction>Any <term refersTo="#term-spray_area" id="trm324">spray area</term> or spray booth referred to in subsection (1) must be:</listIntroduction>
                <item id="section-25.2.list0.a">
                  <num>(a)</num>
                  <p>constructed and equipped in accordance with the General Safety Regulations promulgated in terms of the Occupational Health and Safety Act, 1993 (<ref href="/za/act/1993/85">Act No. 85 of 1993</ref>); and</p>
                </item>
                <item id="section-25.2.list0.b">
                  <num>(b)</num>
                  <p>approved by the <term refersTo="#term-authorised_official" id="trm325">authorised official</term>, for emissions, mechanical ventilation, noise and any other relevant Department as may be required by any other law.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.3">
            <num>(3)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm326">person</term> conducting sand blasting, shot blasting, grinding, finishing or similar activity which customarily produces emissions of <term refersTo="#term-dust" id="trm327">dust</term> that may be harmful to public health, or cause a <term refersTo="#term-nuisance" id="trm328">nuisance</term>, shall take the <term refersTo="#term-best_practicable_environmental_option" id="trm329">best practicable environmental option</term> to prevent emissions into the <term refersTo="#term-atmosphere" id="trm330">atmosphere</term> to the satisfaction of the authorised official.</p>
            </content>
          </subsection>
          <subsection id="section-25.4">
            <num>(4)</num>
            <content>
              <blockList id="section-25.4.list0">
                <listIntroduction>Any <term refersTo="#term-person" id="trm331">person</term> undertaking an activity referred to in subsection (3) must implement at least the following control measures:</listIntroduction>
                <item id="section-25.4.list0.a">
                  <num>(a)</num>
                  <p><term refersTo="#term-dust" id="trm332">dust</term> extraction control measures;</p>
                </item>
                <item id="section-25.4.list0.b">
                  <num>(b)</num>
                  <p>any alternative control measure approved by the <term refersTo="#term-air_quality_officer" id="trm333">air quality officer</term> or his or he delegated representative.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-25.5">
            <num>(5)</num>
            <content>
              <p>An occupier or owner of any <term refersTo="#term-premises" id="trm334">premises</term> must prevent the existence in, or emission of any <term refersTo="#term-air_pollution" id="trm335">air pollution</term> <term refersTo="#term-nuisance" id="trm336">nuisance</term> from, his or her <term refersTo="#term-premises" id="trm337">premises</term>.</p>
            </content>
          </subsection>
          <subsection id="section-25.6">
            <num>(6)</num>
            <content>
              <p>The occupier or owner of any <term refersTo="#term-premises" id="trm338">premises</term> from which an <term refersTo="#term-air_pollution" id="trm339">air pollution</term> <term refersTo="#term-nuisance" id="trm340">nuisance</term> emanates, or where an <term refersTo="#term-air_pollution" id="trm341">air pollution</term> <term refersTo="#term-nuisance" id="trm342">nuisance</term> exists, is guilty of an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-26">
          <num>26.</num>
          <heading>Dust emissions</heading>
          <subsection id="section-26.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm343">person</term> who conducts any activity or omits to conduct any activity which causes or permits <term refersTo="#term-dust" id="trm344">dust</term> emissions into the <term refersTo="#term-atmosphere" id="trm345">atmosphere</term> that may be harmful to public health and well-being or is likely to cause a <term refersTo="#term-nuisance" id="trm346">nuisance</term> to persons residing or present in the vicinity of such land, activity or <term refersTo="#term-premises" id="trm347">premises</term> shall adopt the best practical environmental option to the satisfaction of the authorised official, to prevent and abate <term refersTo="#term-dust" id="trm348">dust</term> emissions.</p>
            </content>
          </subsection>
          <subsection id="section-26.2">
            <num>(2)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm349">authorised official</term> may require any <term refersTo="#term-person" id="trm350">person</term> suspected of causing a <term refersTo="#term-dust" id="trm351">dust</term> <term refersTo="#term-nuisance" id="trm352">nuisance</term> to submit a <term refersTo="#term-dust" id="trm353">dust</term> management plan within the time period specified in the written notice.</p>
            </content>
          </subsection>
          <subsection id="section-26.3">
            <num>(3)</num>
            <content>
              <blockList id="section-26.3.list0">
                <listIntroduction>The <term refersTo="#term-dust" id="trm354">dust</term> management plan contemplated in subsection (2) must:</listIntroduction>
                <item id="section-26.3.list0.a">
                  <num>(a)</num>
                  <p>identify all possible sources of <term refersTo="#term-dust" id="trm355">dust</term> within the affected site;</p>
                </item>
                <item id="section-26.3.list0.b">
                  <num>(b)</num>
                  <p>detail the best practicable measures to be undertaken to mitigate <term refersTo="#term-dust" id="trm356">dust</term> emissions;</p>
                </item>
                <item id="section-26.3.list0.c">
                  <num>(c)</num>
                  <p>detail an implementation schedule;</p>
                </item>
                <item id="section-26.3.list0.d">
                  <num>(d)</num>
                  <p>identify the <term refersTo="#term-person" id="trm357">person</term> responsible for implementation of the measures;</p>
                </item>
                <item id="section-26.3.list0.e">
                  <num>(e)</num>
                  <p>incorporate a dustfall monitoring plan; and</p>
                </item>
                <item id="section-26.3.list0.f">
                  <num>(f)</num>
                  <p>establish a register for recording all complaints received by the persons regarding dustfall, and for recording follow up actions and responses to the complaints.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-26.4">
            <num>(4)</num>
            <content>
              <p>The <term refersTo="#term-authorised_official" id="trm358">authorised official</term> may require additional measures to be detailed in the <term refersTo="#term-dust" id="trm359">dust</term> management plan.</p>
            </content>
          </subsection>
          <subsection id="section-26.5">
            <num>(5)</num>
            <content>
              <p>The <term refersTo="#term-dust" id="trm360">dust</term> management plan must be implemented within a time period specified by the authorised official in a written notice.</p>
            </content>
          </subsection>
          <subsection id="section-26.6">
            <num>(6)</num>
            <content>
              <p>Failure to comply with the provisions of this section constitutes an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-27">
          <num>27.</num>
          <heading>Steps to abate <term refersTo="#term-nuisance" id="trm361">nuisance</term></heading>
          <paragraph id="section-27.paragraph0">
            <content>
              <p>At any time, the <term refersTo="#term-City" id="trm362">City</term> may at its own cost take whatever steps it considers necessary in order to remedy the harm caused by the <term refersTo="#term-nuisance" id="trm363">nuisance</term> and prevent a recurrence of it, and may recover the reasonable costs incurred from the <term refersTo="#term-person" id="trm364">person</term> responsible for causing the <term refersTo="#term-nuisance" id="trm365">nuisance</term>.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-X">
        <num>X</num>
        <heading>General matters</heading>
        <section id="section-28">
          <num>28.</num>
          <heading>Compliance notice</heading>
          <subsection id="section-28.1">
            <num>(1)</num>
            <content>
              <blockList id="section-28.1.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" id="trm366">authorised official</term> may serve a compliance notice on any <term refersTo="#term-person" id="trm367">person</term> whom he or she reasonably believes is likely to act contrary to, or has acted in contravention of the By-law, calling upon that <term refersTo="#term-person" id="trm368">person</term> -</listIntroduction>
                <item id="section-28.1.list0.a">
                  <num>(a)</num>
                  <p>to comply with the relevant section of the By-law;</p>
                </item>
                <item id="section-28.1.list0.b">
                  <num>(b)</num>
                  <p>to take all necessary steps to prevent a recurrence of the non-compliance; and</p>
                </item>
                <item id="section-28.1.list0.c">
                  <num>(c)</num>
                  <p>to comply with any other conditions contained in the notice.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-28.2">
            <num>(2)</num>
            <content>
              <blockList id="section-28.2.list0">
                <listIntroduction>A compliance notice under subsection (1) may be served -</listIntroduction>
                <item id="section-28.2.list0.a">
                  <num>(a)</num>
                  <blockList id="section-28.2.list0.a.list0">
                    <listIntroduction>upon the occupier, manager or owner of any <term refersTo="#term-premises" id="trm369">premises</term>, by -</listIntroduction>
                    <item id="section-28.2.list0.a.list0.i">
                      <num>(i)</num>
                      <p>delivering it to the occupier, manager or owner or, if the owner cannot be traced or is living abroad, the agent of the owner;</p>
                    </item>
                    <item id="section-28.2.list0.a.list0.ii">
                      <num>(ii)</num>
                      <p>transmitting it by registered post to the last known address of the owner or the last known address of the agent; or</p>
                    </item>
                    <item id="section-28.2.list0.a.list0.iii">
                      <num>(iii)</num>
                      <p>delivering it to the address where the <term refersTo="#term-premises" id="trm370">premises</term> are situated, if the address of the owner and the address of the agent are unknown;</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-28.3">
            <num>(3)</num>
            <content>
              <p>Failure to comply with a compliance notice constitutes an offence.</p>
            </content>
          </subsection>
        </section>
        <section id="section-29">
          <num>29.</num>
          <heading>Enforcement</heading>
          <subsection id="section-29.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" id="trm371">authorised official</term> must take all lawful, necessary and reasonable practicable measures to enforce the provisions of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-29.2">
            <num>(2)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm372">City</term> may develop enforcement procedures which should take into consideration any national or provincial enforcement procedures.</p>
            </content>
          </subsection>
        </section>
        <section id="section-30">
          <num>30.</num>
          <heading>Appeals</heading>
          <subsection id="section-30.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm373">person</term> may appeal against a decision taken by an authorised official under this By-law by giving a written notice of the appeal in accordance with the provisions of section 62 of the <term refersTo="#term-Municipal_Systems_Act" id="trm374">Municipal Systems Act</term>.</p>
            </content>
          </subsection>
        </section>
        <section id="section-31">
          <num>31.</num>
          <heading>Exemptions</heading>
          <subsection id="section-31.1">
            <num>(1)</num>
            <content>
              <p>Any <term refersTo="#term-person" id="trm375">person</term> may apply to the <term refersTo="#term-City" id="trm376">City</term>, in writing, for exemption from the application of a provision of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-31.2">
            <num>(2)</num>
            <content>
              <blockList id="section-31.2.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm377">City</term> may-</listIntroduction>
                <item id="section-31.2.list0.a">
                  <num>(a)</num>
                  <p>approve or refuse an application for exemption; and</p>
                </item>
                <item id="section-31.2.list0.b">
                  <num>(b)</num>
                  <p>impose conditions when granting approval for applications for exemption, made in terms of subsection (1).</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.3">
            <num>(3)</num>
            <content>
              <p>An application in terms of subsection (1) must be accompanied by substantive reasons.</p>
            </content>
          </subsection>
          <subsection id="section-31.4">
            <num>(4)</num>
            <content>
              <p>The <term refersTo="#term-City" id="trm378">City</term> may require an applicant applying for exemption to take appropriate steps to bring the application to the attention of relevant interested and affected persons and the public.</p>
            </content>
          </subsection>
          <subsection id="section-31.5">
            <num>(5)</num>
            <content>
              <blockList id="section-31.5.list0">
                <listIntroduction>The steps contemplated in subsection (4) must include the publication of a notice in at least two newspapers, one circulating provincially and one circulating within the jurisdiction of the <term refersTo="#term-City" id="trm379">City</term>-</listIntroduction>
                <item id="section-31.5.list0.a">
                  <num>(a)</num>
                  <p>giving reasons for the application; and</p>
                </item>
                <item id="section-31.5.list0.b">
                  <num>(b)</num>
                  <p>containing such other particulars concerning the application as the <term refersTo="#term-air_quality_officer" id="trm380">air quality officer</term> may require.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.6">
            <num>(6)</num>
            <content>
              <blockList id="section-31.6.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm381">City</term> may -</listIntroduction>
                <item id="section-31.6.list0.a">
                  <num>(a)</num>
                  <p>from time to time review any exemption granted in terms of this section, and may impose such conditions as it may determine; and</p>
                </item>
                <item id="section-31.6.list0.b">
                  <num>(b)</num>
                  <p>on good grounds withdraw any exemption.</p>
                </item>
              </blockList>
            </content>
          </subsection>
          <subsection id="section-31.7">
            <num>(7)</num>
            <content>
              <blockList id="section-31.7.list0">
                <listIntroduction>The <term refersTo="#term-City" id="trm382">City</term> may not grant an exemption under subsection (1) until the <term refersTo="#term-City" id="trm383">City</term> has:</listIntroduction>
                <item id="section-31.7.list0.a">
                  <num>(a)</num>
                  <p>taken reasonable measures to ensure that all persons whose rights may be detrimentally affected by the granting of the exemption, including adjacent land owners or occupiers, are aware of the application for exemption.</p>
                </item>
                <item id="section-31.7.list0.b">
                  <num>(b)</num>
                  <p>provided such persons with a reasonable opportunity to object to the application; and</p>
                </item>
                <item id="section-31.7.list0.c">
                  <num>(c)</num>
                  <p>duly considered and taken into account any reasonable objections raised.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-32">
          <num>32.</num>
          <heading>Indemnity</heading>
          <paragraph id="section-32.paragraph0">
            <content>
              <p>The <term refersTo="#term-City" id="trm384">City</term> shall not be liable for any damage caused to any property or <term refersTo="#term-premises" id="trm385">premises</term> by any action or omission on the part of the employees or officials of the <term refersTo="#term-City" id="trm386">City</term> when exercising any function or performing any duty in terms of this By-law, provided that such employees or officials must, when exercising such function or performing such duty, take reasonable steps to prevent any damage to such property or <term refersTo="#term-premises" id="trm387">premises</term>.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <chapter id="chapter-XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <hcontainer id="chapter-XI.hcontainer_1" name="crossheading">
          <heading>First in chapter</heading>
        </hcontainer>
        <section id="section-33">
          <num>33.</num>
          <heading>Offences and penalties</heading>
          <subsection id="section-33.1">
            <num>(1)</num>
            <content>
              <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
            </content>
          </subsection>
          <subsection id="section-33.2">
            <num>(2)</num>
            <content>
              <p>Any person who is guilty of an offence in terms of this By-law is liable to a fine or, upon conviction to, imprisonment not exceeding 1 year or to both such fine and such imprisonment.</p>
            </content>
          </subsection>
          <subsection id="section-33.3">
            <num>(3)</num>
            <content>
              <p>Any person who commits a continuing offence may be liable to a fine for each day during which that person fails to comply with a directive, compliance notice or repair notice, issued in terms of this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-33.4">
            <num>(4)</num>
            <content>
              <p>It is an offence to supply false information to an authorised official in respect of any issue pertaining to this By-law.</p>
            </content>
          </subsection>
          <subsection id="section-33.5">
            <num>(5)</num>
            <content>
              <p>Where no specific penalty is provided, any person committing an offence in terms of this By-law is liable to a fine and upon conviction to imprisonment for a period not exceeding one (1) year or to both such imprisonment and such fine.</p>
            </content>
          </subsection>
          <subsection id="section-33.6">
            <num>(6)</num>
            <content>
              <blockList id="section-33.6.list0">
                <listIntroduction>In addition to imposing a fine or imprisonment, a court may order any person convicted of an offence under this By-law -</listIntroduction>
                <item id="section-33.6.list0.a">
                  <num>(a)</num>
                  <p>to remedy the harm caused; and</p>
                </item>
                <item id="section-33.6.list0.b">
                  <num>(b)</num>
                  <p>to pay damages for harm caused to another person or to property.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section id="section-34">
          <num>34.</num>
          <heading>Repeal and savings</heading>
          <subsection id="section-34.1">
            <num>(1)</num>
            <content>
              <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
            </content>
          </subsection>
          <subsection id="section-34.2">
            <num>(2)</num>
            <content>
              <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
            </content>
          </subsection>
          <hcontainer id="section-34.hcontainer_1" name="crossheading">
            <heading>Second in chapter</heading>
          </hcontainer>
        </section>
        <section id="section-35">
          <num>35.</num>
          <heading>Short title</heading>
          <paragraph id="section-35.paragraph0">
            <content>
              <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management"/>
              <FRBRalias value="Schedule 1"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17/schedule1"/>
              <FRBRuri value="/za-cpt/act/by-law/2016/air-quality-management/eng@2016-08-17"/>
              <FRBRdate date="2019-12-05" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <heading>Schedule 1</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.hcontainer_1" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule1.hcontainer_2" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <paragraph id="schedule1.paragraph1">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta>
          <identification source="#slaw">
            <FRBRWork>
              <FRBRthis value="/za/act/1980/01/schedule2"/>
              <FRBRuri value="/za/act/1980/01"/>
              <FRBRalias value="Schedule 2"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRcountry value="za"/>
            </FRBRWork>
            <FRBRExpression>
              <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="1980-01-01" name="Generation"/>
              <FRBRauthor href="#council"/>
              <FRBRlanguage language="eng"/>
            </FRBRExpression>
            <FRBRManifestation>
              <FRBRthis value="/za/act/1980/01/eng@/schedule2"/>
              <FRBRuri value="/za/act/1980/01/eng@"/>
              <FRBRdate date="2020-05-21" name="Generation"/>
              <FRBRauthor href="#slaw"/>
            </FRBRManifestation>
          </identification>
        </meta>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>Good management practices to prevent or minimise the discharge of smoke from open burning of vegetation</subheading>
            <paragraph id="schedule2.paragraph-1">
              <num>1.</num>
              <content>
                <p>Consider alternatives to burning – e.g. mulching for recovery of nutrient value, drying for recovery as firewood.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-2">
              <num>2.</num>
              <content>
                <p>Vegetation that is to be burned (such as trimmings, pruning or felling’s cut from active growth) should as a general guide be allowed to dry to brown appearance prior to burning.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.hcontainer_1" name="crossheading">
              <heading>Here's one</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-3">
              <num>3.</num>
              <content>
                <p>Except for tree stumps or crop stubble, the place of combustion should be at least 50 metres from any road other than a highway, and 100 metres from any highway or dwelling on a neighbouring property.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-4">
              <num>4.</num>
              <content>
                <p>Due regard should be given to direction and strength of wind, and quantity and state of vegetation to be combusted, prior to initiating combustion.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-5">
              <num>5.</num>
              <content>
                <p>In the case of vegetation previously treated by spray with any agrichemical, any manufacturer's instructions as on the label of any container in respect of the burning of treated vegetation must be observed.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule2.hcontainer_2" name="crossheading">
              <heading>And another</heading>
            </hcontainer>
            <hcontainer id="schedule2.hcontainer_3" name="crossheading">
              <heading>And more</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph-6">
              <num>6.</num>
              <content>
                <p>Two days' fine weather should be allowed prior to burning.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-7">
              <num>7.</num>
              <content>
                <p>Vegetation should be stacked loosely rather than compacted.</p>
              </content>
            </paragraph>
            <paragraph id="schedule2.paragraph-8">
              <num>8.</num>
              <content>
                <p>A small fire, started with the driest material, with further material continually fed onto it once it is blazing, is preferable to a large stack ignited and left unattended.</p>
                <p><b>Note:</b> Persons conducting open burning of vegetation must ensure compliance with the requirements of the National Veld and Forest Fire Act, 1998, (<ref href="/za/act/1998/101">Act No. 101 of 1998</ref>) as amended.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>""",
            output
        )

        # check mappings
        self.assertEqual(
            {
                "chapter-XI.crossheading-0": "chapter-XI.hcontainer_1",
                "section-34.crossheading-0": "section-34.hcontainer_1",
                "schedule1.crossheading-0": "schedule1.hcontainer_1",
                "schedule1.crossheading-1": "schedule1.hcontainer_2",
                "schedule2.crossheading-0": "schedule2.hcontainer_1",
                "schedule2.crossheading-1": "schedule2.hcontainer_2",
                "schedule2.crossheading-2": "schedule2.hcontainer_3",
            },
            mappings
        )

        # check annotations
        # ?

    def test_para_to_hcontainer(self):
        migration = UnnumberedParagraphsToHcontainer()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <paragraph id="section-1.paragraph0">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.paragraph0.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.paragraph0.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.paragraph0.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.paragraph0.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.paragraph0.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.paragraph0.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList id="section-1.paragraph0.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.paragraph0.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.paragraph0.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </paragraph>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <paragraph id="section-2.paragraph0">
            <content>
              <p>One paragraph.</p>
            </content>
          </paragraph>
          <paragraph id="section-2.paragraph1">
            <content>
              <p>Another paragraph.</p>
            </content>
          </paragraph>
        </section>
      </chapter>
      <section id="section-2">
        <num>2.</num>
        <paragraph id="section-2.paragraph0">
          <content>
            <blockList id="section-2.paragraph0.list0">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item id="section-2.paragraph0.list0.a">
                <num>(a)</num>
                <blockList id="section-2.paragraph0.list0.a.list0">
                  <listIntroduction>aye</listIntroduction>
                  <item id="section-2.paragraph0.list0.a.list0.i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </paragraph>
        <paragraph id="section-2.paragraph1">
          <content>
            <p>hi</p>
          </content>
        </paragraph>
      </section>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule3">
      <doc name="schedule3">
        <meta/>
        <mainBody>
          <hcontainer id="schedule3" name="schedule">
            <heading>Schedule 3</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule3.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <paragraph id="schedule3.paragraph0">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <paragraph id="schedule3.paragraph1">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>
    """)
        migration.migrate_document(doc)
        doc.refresh_xml()
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <chapter id="chapter-I">
        <num>I</num>
        <heading>Definitions and fundamental principles</heading>
        <section id="section-1">
          <num>1.</num>
          <heading>Definitions</heading>
          <hcontainer id="section-1.hcontainer_1">
            <content>
              <p>In this By-law, unless the context indicates otherwise -</p>
              <p refersTo="#term-Council">"<def refersTo="#term-Council">Council</def>" means the Municipal Council of the <term refersTo="#term-City" id="trm20">City</term>;</p>
              <blockList id="section-1.hcontainer_1.list0" refersTo="#term-dark_smoke">
                <listIntroduction>"<def refersTo="#term-dark_smoke">dark smoke</def>" means-</listIntroduction>
                <item id="section-1.hcontainer_1.list0.a">
                  <num>(a)</num>
                  <p>in respect of Chapter V and Chapter VI of this By-law, <term refersTo="#term-smoke" id="trm21">smoke</term> which, when measured using a <term refersTo="#term-light_absorption_meter" id="trm22">light absorption meter</term>, <term refersTo="#term-obscuration" id="trm23">obscuration</term> measuring equipment or other similar equipment, has an <term refersTo="#term-obscuration" id="trm24">obscuration</term> of 20% or greater;</p>
                </item>
                <item id="section-1.hcontainer_1.list0.b">
                  <num>(b)</num>
                  <blockList id="section-1.hcontainer_1.list0.b.list0">
                    <listIntroduction>in respect of Chapter VIII of this By-law –</listIntroduction>
                    <item id="section-1.hcontainer_1.list0.b.list0.i">
                      <num>(i)</num>
                      <p><term refersTo="#term-smoke" id="trm25">smoke</term> emitted from the exhaust outlets of naturally aspirated compression ignition engines which has a density of 50 Hartridge <term refersTo="#term-smoke" id="trm26">smoke</term> units or more or a light absorption co-efficient of more than 1,61 mï1 ; or 18,57 percentage opacity; and</p>
                    </item>
                    <item id="section-1.hcontainer_1.list0.b.list0.ii">
                      <num>(ii)</num>
                      <p><term refersTo="#term-smoke" id="trm27">smoke</term> emitted from the exhaust outlets of turbo-charged compression ignition engines which has a density of 56 Hartridge <term refersTo="#term-smoke" id="trm28">smoke</term> units or more or a light absorption co-efficient of more than 1,91 mï1 ; or 21,57 percentage opacity.</p>
                    </item>
                  </blockList>
                </item>
              </blockList>
              <blockList id="section-1.hcontainer_1.list3" refersTo="#term-nuisance">
                <listIntroduction>"<def refersTo="#term-nuisance">nuisance</def>" means an unreasonable interference or likely interference caused by <term refersTo="#term-air_pollution" id="trm37">air pollution</term> which has an adverse impact on -</listIntroduction>
                <item id="section-1.hcontainer_1.list3.a">
                  <num>(a)</num>
                  <p>the health or well-being of any <term refersTo="#term-person" id="trm38">person</term> or <term refersTo="#term-living_organism" id="trm39">living organism</term>; or</p>
                </item>
                <item id="section-1.hcontainer_1.list3.b">
                  <num>(b)</num>
                  <p>the use and enjoyment by an owner or occupier of his or her property or the <term refersTo="#term-environment" id="trm40">environment</term>;</p>
                </item>
              </blockList>
            </content>
          </hcontainer>
        </section>
        <section id="section-2">
          <num>2.</num>
          <heading>Application of this By-law</heading>
          <hcontainer id="section-2.hcontainer_1">
            <content>
              <p>One paragraph.</p>
            </content>
          </hcontainer>
          <hcontainer id="section-2.hcontainer_2">
            <content>
              <p>Another paragraph.</p>
            </content>
          </hcontainer>
        </section>
      </chapter>
      <section id="section-2">
        <num>2.</num>
        <hcontainer id="section-2.hcontainer_1">
          <content>
            <blockList id="section-2.hcontainer_1.list0">
              <listIntroduction>aoeuaoeu</listIntroduction>
              <item id="section-2.hcontainer_1.list0.a">
                <num>(a)</num>
                <blockList id="section-2.hcontainer_1.list0.a.list0">
                  <listIntroduction>aye</listIntroduction>
                  <item id="section-2.hcontainer_1.list0.a.list0.i">
                    <num>(i)</num>
                    <p>eye</p>
                  </item>
                </blockList>
              </item>
            </blockList>
          </content>
        </hcontainer>
        <hcontainer id="section-2.hcontainer_2">
          <content>
            <p>hi</p>
          </content>
        </hcontainer>
      </section>
    </body>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <hcontainer id="schedule1.hcontainer_1">
              <content>
                <p>schedule 1</p>
              </content>
            </hcontainer>
            <paragraph id="schedule1.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule1.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <hcontainer id="schedule2.hcontainer_2">
              <content>
                <p>hi</p>
              </content>
            </hcontainer>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule3">
      <doc name="schedule3">
        <meta/>
        <mainBody>
          <hcontainer id="schedule3" name="schedule">
            <heading>Schedule 3</heading>
            <subheading>Standards and specifications for fuel-burning equipment:</subheading>
            <paragraph id="schedule3.paragraph-1">
              <num>1.</num>
              <content>
                <p>All fuel-burning equipment capable of burning more than 100kg/h of coal, biomass or other solid fuel shall be fitted with suitable control equipment so as to limit dust and grit emissions.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-2">
              <num>2.</num>
              <content>
                <p>The control equipment shall be fitted in such a manner so as to facilitate easy maintenance.</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-3">
              <num>3.</num>
              <content>
                <p>The permitted concentration of grit and dust emissions from a chimney serving a coal fired boiler equipped with any mechanical draught fan system shall not be more than 250 mg/Nm³ (as measured at 0°C, 101,3 kPa and 12% CO₂). Where the fuel-burning equipment has been declared as a Controlled Emitter in terms of the Air Quality Act, the respective Controlled Emitter Regulations shall apply.</p>
                <p>The approved methods for testing shall be:</p>
                <p>US EPA:</p>
                <p>1. Method 17 - In-Stack Particulate (PM).</p>
                <p>2. Method 5 - Particulate Matter (PM).</p>
                <p>ISO standards:</p>
                <p>ISO 9096: Stationary source emissions - Manual Determination of mass concentration of particulate matter.</p>
                <p>British standards:</p>
                <p>BS 3405:1983 Method for measurement of particulate emission including grit and dust (simplified method).</p>
              </content>
            </paragraph>
            <paragraph id="schedule3.paragraph-4">
              <num>4.</num>
              <content>
                <p>The City reserves the right to call upon the owner or his or her agent of the fuel burning equipment to have the emissions from such fuel burning equipment evaluated at his or her own expense as may be required by the authorised official.</p>
              </content>
            </paragraph>
            <hcontainer id="schedule3.crossheading-0" name="crossheading">
              <heading>Insulation of chimneys:</heading>
            </hcontainer>
            <hcontainer id="schedule3.hcontainer_2">
              <content>
                <p>All fuel-burning equipment using Heavy Fuel Oil or other liquid fuels with a sulphur content equal to or greater than 2.5 % by weight must be fitted with a fully insulated chimney using either a 25mm air gap or mineral wool insulation to prevent the formation of acid smut. Such chimneys must be maintained in a good state of repair at all times.</p>
              </content>
            </hcontainer>
            <hcontainer id="schedule3.crossheading-1" name="crossheading">
              <heading>Wood-fired pizza ovens and other solid fuel combustion equipment:</heading>
            </hcontainer>
            <hcontainer id="schedule3.hcontainer_4">
              <content>
                <p>Wood-fired pizza ovens and other solid fuel combustion equipment shall be fitted with induced draft fans at the discretion of the authorised official.</p>
              </content>
            </hcontainer>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>""",
            doc.document_xml)

    def test_component_to_attachment(self):
        migration = ComponentSchedulesToAttachments()

        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body/>
  </act>
  <components>
    <component id="component-schedule1">
      <doc name="schedule1">
        <meta/>
        <mainBody>
          <hcontainer id="schedule1" name="schedule">
            <subheading>Subheading</subheading>
            <paragraph id="schedule1.paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
    <component id="component-schedule2">
      <doc name="schedule2">
        <meta/>
        <mainBody>
          <hcontainer id="schedule2" name="schedule">
            <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <hcontainer id="schedule2.crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="schedule2.paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </hcontainer>
        </mainBody>
      </doc>
    </component>
  </components>
</akomaNtoso>""")
        migration.migrate_document(doc)
        xml = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual("""<akomaNtoso xmlns="http://www.akomantoso.org/2.0">
  <act contains="originalVersion">
    <meta/>
    <body/>
  <attachments>
    <attachment id="att_1">
      <subheading>Subheading</subheading>
            <doc name="schedule">
        <meta/>
        <mainBody>
          <paragraph id="paragraph0">
              <content>
                <p>schedule 1</p>
              </content>
            </paragraph>
          </mainBody>
      </doc>
    </attachment>
    <attachment id="att_2">
      <heading>Schedule 2</heading>
            <subheading>REPEAL OR AMENDMENT OF LAWS</subheading>
            <doc name="schedule">
        <meta/>
        <mainBody>
          <hcontainer id="crossheading-0" name="crossheading">
              <heading>(Section 45(1))</heading>
            </hcontainer>
            <paragraph id="paragraph0">
              <content>
                <p>hi</p>
              </content>
            </paragraph>
          </mainBody>
      </doc>
    </attachment>
  </attachments>
</act>
  </akomaNtoso>
""", xml)

    def test_eid_basic(self):
        """ includes basic checks for
        meta elements,
        chapter, part, subpart, section, subsection, list, item
        """
        migration = AKNeId()

        doc = Document(work=self.work, document_xml="""
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
      <lifecycle source="#OpenByLaws-org-za">
        <eventRef id="amendment-2011-08-05" date="2011-08-05" type="amendment" source="#amendment-0-source"/>
        <eventRef id="amendment-2013-11-01" date="2013-11-01" type="amendment" source="#amendment-1-source"/>
        <eventRef id="amendment-2016-11-04" date="2016-11-04" type="amendment" source="#amendment-2-source"/>
      </lifecycle>
      <references source="#this">
        <TLCOrganization id="slaw" href="https://github.com/longhotsummer/slaw" showAs="Slaw"/>
        <TLCOrganization id="council" href="/ontology/organization/za/council" showAs="Council"/>
        <TLCTerm id="term-aerodrome" showAs="aerodrome" href="/ontology/term/this.eng.aerodrome"/>
        <TLCTerm id="term-taxiway" showAs="taxiway" href="/ontology/term/this.eng.taxiway"/>
        <passiveRef id="amendment-0-source" href="/za-cpt/act/by-law/2011/sub-council-further-amendment" showAs="Cape Town Sub-council Further Amendment By-law, 2011"/>
        <passiveRef id="amendment-1-source" href="/za-cpt/act/by-law/2013/sub-council-amendment" showAs="Sub-council: Amendment"/>
        <passiveRef id="amendment-2-source" href="/za-cpt/act/by-law/2016/sub-council-amendment" showAs="Sub-Council: Amendment"/>
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
        <hcontainer id="section-1.hcontainer_1">
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
      <chapter id="chapter-XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <subpart id="chapter-XI.subpart-1">
          <num>1</num>
          <heading>First subpart</heading>
          <section id="section-33">
            <num>33.</num>
            <heading>Offences and penalties</heading>
            <subsection id="section-33.1">
              <num>(1)</num>
              <content>
                <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
              </content>
            </subsection>
            <subsection id="section-33.6">
              <num>(6)</num>
              <content>
                <blockList id="section-33.6.list0">
                  <listIntroduction>In addition ... under this By-law -</listIntroduction>
                  <item id="section-33.6.list0.a">
                    <num>(a)</num>
                    <p>to remedy the harm caused; and</p>
                  </item>
                  <item id="section-33.6.list0.b">
                    <num>(b)</num>
                    <p>to pay damages for harm caused to another person or to property.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
          </section>
        </subpart>
        <subpart id="chapter-XI.subpart-2">
          <num>2</num>
          <heading>Second subpart</heading>
          <section id="section-34">
            <num>34.</num>
            <heading>Repeal and savings</heading>
            <subsection id="section-34.1">
              <num>(1)</num>
              <content>
                <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
              </content>
            </subsection>
            <subsection id="section-34.2">
              <num>(2)</num>
              <content>
                <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
              </content>
            </subsection>
          </section>
          <section id="section-35">
            <num>35.</num>
            <heading>Short title</heading>
            <hcontainer id="section-35.hcontainer_1">
              <content>
                <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
              </content>
            </hcontainer>
          </section>
        </subpart>
      </chapter>
    </body>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
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
      <lifecycle source="#OpenByLaws-org-za">
        <eventRef date="2011-08-05" type="amendment" source="#amendment-0-source" eId="amendment-2011-08-05"/>
        <eventRef date="2013-11-01" type="amendment" source="#amendment-1-source" eId="amendment-2013-11-01"/>
        <eventRef date="2016-11-04" type="amendment" source="#amendment-2-source" eId="amendment-2016-11-04"/>
      </lifecycle>
      <references source="#this">
        <TLCOrganization href="https://github.com/longhotsummer/slaw" showAs="Slaw" eId="slaw"/>
        <TLCOrganization href="/ontology/organization/za/council" showAs="Council" eId="council"/>
        <TLCTerm showAs="aerodrome" href="/ontology/term/this.eng.aerodrome" eId="term-aerodrome"/>
        <TLCTerm showAs="taxiway" href="/ontology/term/this.eng.taxiway" eId="term-taxiway"/>
        <passiveRef href="/za-cpt/act/by-law/2011/sub-council-further-amendment" showAs="Cape Town Sub-council Further Amendment By-law, 2011" eId="amendment-0-source"/>
        <passiveRef href="/za-cpt/act/by-law/2013/sub-council-amendment" showAs="Sub-council: Amendment" eId="amendment-1-source"/>
        <passiveRef href="/za-cpt/act/by-law/2016/sub-council-amendment" showAs="Sub-Council: Amendment" eId="amendment-2-source"/>
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
        <hcontainer eId="sec_1__hcontainer_1">
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
            <blockList eId="sec_2__subsec_1__list_1">
              <listIntroduction>The Caretaker may-</listIntroduction>
              <item eId="sec_2__subsec_1__list_1__item_a">
                <num>(a)</num>
                <p>prohibit any person who fails to pay an amount in respect of any facility on the aerodrome of which he makes use after such charges have become payable, to make use of any facility of the aerodrome:</p>
              </item>
              <item eId="sec_2__subsec_1__list_1__item_b">
                <num>(b)</num>
                <p>should he for any reason deem it necessary at any time, for such period as he may determine, prohibit or limit the admission of people or vehicles, or both, to the aerodrome or to any particular area thereof;</p>
              </item>
              <item eId="sec_2__subsec_1__list_1__item_c">
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
      <chapter eId="chp_XI">
        <num>XI</num>
        <heading>Offences and penalties</heading>
        <subpart eId="chp_XI__subpart_1">
          <num>1</num>
          <heading>First subpart</heading>
          <section eId="sec_33">
            <num>33.</num>
            <heading>Offences and penalties</heading>
            <subsection eId="sec_33__subsec_1">
              <num>(1)</num>
              <content>
                <p>A person who contravenes sections <ref href="#section-4">4</ref>(1) and (2), <ref href="#section-6">6</ref>(3), <ref href="#section-10">10</ref>(1) and (2), <ref href="#section-11">11</ref>(1), <ref href="#section-12">12</ref>(1), <ref href="#section-19">19</ref>(1), <ref href="#section-19">19</ref>(3), <ref href="#section-20">20</ref>(1), <ref href="#section-20">20</ref>(2), <ref href="#section-21">21</ref>(1), <ref href="#section-22">22</ref>(1), <ref href="#section-24">24</ref>(1), <ref href="#section-25">25</ref>(3), (4) , (5) and (6) , <ref href="#section-26">26</ref>(1), (2), (3) and (5), <ref href="#section-28">28</ref>(1), (2) and (3) is guilty of an offence.</p>
              </content>
            </subsection>
            <subsection eId="sec_33__subsec_6">
              <num>(6)</num>
              <content>
                <blockList eId="sec_33__subsec_6__list_1">
                  <listIntroduction>In addition ... under this By-law -</listIntroduction>
                  <item eId="sec_33__subsec_6__list_1__item_a">
                    <num>(a)</num>
                    <p>to remedy the harm caused; and</p>
                  </item>
                  <item eId="sec_33__subsec_6__list_1__item_b">
                    <num>(b)</num>
                    <p>to pay damages for harm caused to another person or to property.</p>
                  </item>
                </blockList>
              </content>
            </subsection>
          </section>
        </subpart>
        <subpart eId="chp_XI__subpart_2">
          <num>2</num>
          <heading>Second subpart</heading>
          <section eId="sec_34">
            <num>34.</num>
            <heading>Repeal and savings</heading>
            <subsection eId="sec_34__subsec_1">
              <num>(1)</num>
              <content>
                <p>The City of Cape Town: Air Quality Management By-law 2010 is hereby repealed.</p>
              </content>
            </subsection>
            <subsection eId="sec_34__subsec_2">
              <num>(2)</num>
              <content>
                <p>Anything done or deemed to have been done under any other by-law relating to air quality remains valid to the extent that it is consistent with this By-law.</p>
              </content>
            </subsection>
          </section>
          <section eId="sec_35">
            <num>35.</num>
            <heading>Short title</heading>
            <hcontainer eId="sec_35__hcontainer_1">
              <content>
                <p>This By-law is called the City of Cape Town: Air Quality Management By-law, 2016.</p>
              </content>
            </hcontainer>
          </section>
        </subpart>
      </chapter>
    </body>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_item(self):
        """ includes checks for list, item, and nested lists
        """
        migration = AKNeId()
        doc = Document(work=self.work, document_xml="""
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
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="originalVersion">
    <meta/>
    <body>
      <section eId="sec_100">
        <subsection eId="sec_100__subsec_3A-2">
          <blockList eId="sec_100__subsec_3A-2__list_7">
            <item eId="sec_100__subsec_3A-2__list_7__item_i">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_7__item_ii-c">
              <p>item text</p>
            </item>
            <item eId="sec_100__subsec_3A-2__list_7__item_iii">
              <blockList eId="sec_100__subsec_3A-2__list_7__item_iii__list_1">
                <item eId="sec_100__subsec_3A-2__list_7__item_iii__list_1__item_a">
                  <p>item text</p>
                </item>
                <item eId="sec_100__subsec_3A-2__list_7__item_iii__list_1__item_b-1-i">
                  <p>item text</p>
                </item>
              </blockList>
            </item>
          </blockList>
        </subsection>
      </section>
    </body>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_schedule(self):
        """ includes checks for
        Schedules, annexures, chapter, part, crossheading, anonymous and numbered paragraphs, article, section
        """
        migration = AKNeId()
        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body/>
    <attachments>
      <attachment id="att_1">
        <heading>Annexure</heading>
        <subheading>Things to do during lockdown</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1" name="crossheading">
              <heading>Form A</heading>
            </hcontainer>
            <hcontainer id="hcontainer_2">
              <content>
                <p>I ................. hereby ...............</p>
                <p>Signed</p>
              </content>
            </hcontainer>
            <hcontainer id="hcontainer_3" name="crossheading">
              <heading>Form B</heading>
            </hcontainer>
            <hcontainer id="hcontainer_4">
              <content>
                <p>One may:</p>
              </content>
            </hcontainer>
            <paragraph id="paragraph-1">
              <num>1.</num>
              <content>
                <p>Sing</p>
              </content>
            </paragraph>
            <paragraph id="paragraph-2">
              <num>2.</num>
              <content>
                <p>Dance</p>
              </content>
            </paragraph>
            <paragraph id="paragraph-3">
              <num>3.</num>
              <content>
                <p>Sway</p>
              </content>
            </paragraph>
            <hcontainer id="hcontainer_5" name="crossheading">
              <heading>Form C</heading>
            </hcontainer>
            <section id="section-1">
              <num>1.</num>
              <heading>Paragraph heading</heading>
              <subsection id="section-1.1">
                <num>(1)</num>
                <content>
                  <p>sdfkhsdkjfhldfh.</p>
                </content>
              </subsection>
              <subsection id="section-1.2">
                <num>(2)</num>
                <content>
                  <p>sldfhsdkfnldksn.</p>
                </content>
              </subsection>
            </section>
            <section id="section-2">
              <num>2.</num>
              <heading>Another heading</heading>
              <subsection id="section-2.1">
                <num>(1)</num>
                <content>
                  <p>dskfahsdkfdnsv.dn.</p>
                </content>
              </subsection>
              <subsection id="section-2.2">
                <num>(2)</num>
                <content>
                  <p>sdfkdskvdnvmbdvmsnd.</p>
                </content>
              </subsection>
            </section>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_2">
        <heading>Schedule 1</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1">
              <content>
                <table id="hcontainer_1.table0">
                  <tr>
                    <th>
                      <p>Column 1</p>
                    </th>
                    <th>
                      <p>Column 2</p>
                    </th>
                    <th>
                      <p>Column 3</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>Sub-Council Designation</p>
                    </th>
                    <th>
                      <p>Sub-Council Name</p>
                    </th>
                    <th>
                      <p>Ward Numbers</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>Subcouncil 1 Blaauwberg</p>
                    </td>
                    <td>
                      <p>4, 23, 29, 32, 104, 107</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>Subcouncil 2 Bergdal</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_3">
        <heading>Schedule 2</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1">
              <content>
                <table id="hcontainer_1.table0">
                  <tr>
                    <th>
                      <p>COLUMN 1</p>
                    </th>
                    <th>
                      <p>COLUMN 2</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>SUB-COUNCIL DESIGNATION</p>
                    </th>
                    <th>
                      <p>WARD NUMBERS</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>23, 29, 32 and 104</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 101, 102 and 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_4">
        <heading>Third Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <chapter id="chapter-1">
              <num>1</num>
              <heading>The first Chapter</heading>
              <part id="chapter-1.part-1">
                <num>1</num>
                <heading>The first Part</heading>
                <paragraph id="chapter-1.part-1.paragraph-1">
                  <num>1.</num>
                  <content>
                    <p>The first para</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-1.paragraph-2">
                  <num>2.</num>
                  <content>
                    <p>The second para</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-1.paragraph-345456">
                  <num>345456.</num>
                  <content>
                    <p>The last para</p>
                  </content>
                </paragraph>
              </part>
              <part id="chapter-1.part-2">
                <num>2</num>
                <heading>The second Part</heading>
                <paragraph id="chapter-1.part-2.paragraph-1">
                  <num>1.</num>
                  <content>
                    <p>Starting all over again</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-2.paragraph-2">
                  <num>2.</num>
                  <content>
                    <p>Yup</p>
                  </content>
                </paragraph>
                <paragraph id="chapter-1.part-2.paragraph-3">
                  <num>3.</num>
                  <content>
                    <p>sdflkdsjg;ndfg</p>
                  </content>
                </paragraph>
              </part>
            </chapter>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_5">
        <heading>Fourth Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <part id="part-36">
              <num>36</num>
              <heading>Let's get nested</heading>
              <chapter id="part-36.chapter-A">
                <num>A</num>
                <heading>Nested Chapter</heading>
                <section id="section-1">
                  <num>1.</num>
                  <heading>fjlhsdkfh</heading>
                  <hcontainer id="section-1.hcontainer_1">
                    <content>
                      <p>dsjfhsdkjfhkshdf</p>
                    </content>
                  </hcontainer>
                </section>
                <section id="section-300">
                  <num>300.</num>
                  <heading>skdfhdkshfasd</heading>
                  <hcontainer id="section-300.hcontainer_1">
                    <content>
                      <p>asfjhadjslgfjsdghfjhg</p>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
              <chapter id="part-36.chapter-B">
                <num>B</num>
                <heading>Still inside</heading>
                <section id="section-301">
                  <num>301.</num>
                  <heading>skhfdsjghfd</heading>
                  <hcontainer id="section-301.hcontainer_1">
                    <content>
                      <p>sdfjsdlgjlkdfjg</p>
                    </content>
                  </hcontainer>
                </section>
                <section id="section-302">
                  <num>302.</num>
                  <heading>dkfhdsjhgdbfhjg</heading>
                  <hcontainer id="section-302.hcontainer_1">
                    <content>
                      <blockList id="section-302.hcontainer_1.list0">
                        <listIntroduction>And let's nest a list:</listIntroduction>
                        <item id="section-302.hcontainer_1.list0.1">
                          <num>(1)</num>
                          <p>These ones are weird:</p>
                          <blockList id="section-302.hcontainer_1.list0.1.list0">
                            <listIntroduction><remark status="editorial">[editorial remark]</remark></listIntroduction>
                            <item id="section-302.hcontainer_1.list0.1.list0.a">
                              <num>(a)</num>
                              <p>sfhsdkjfhksdh;</p>
                            </item>
                            <item id="section-302.hcontainer_1.list0.1.list0.b">
                              <num>(b)</num>
                              <p>sdfhsdnfbmnsdbf;</p>
                              <p><remark status="editorial">[editorial remark]</remark></p>
                            </item>
                            <item id="section-302.hcontainer_1.list0.1.list0.c">
                              <num>(c)</num>
                              <p>jshaasbmnbxc.</p>
                            </item>
                          </blockList>
                        </item>
                        <item id="section-302.hcontainer_1.list0.2">
                          <num>(2)</num>
                          <p>A nother not-quite subsection.</p>
                        </item>
                      </blockList>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
            </part>
            <part id="part-37">
              <num>37</num>
              <heading>Back out to the top level</heading>
              <section id="section-303">
                <num>303.</num>
                <heading>sfsjdbfbsdjnfb</heading>
                <subsection id="section-303.1">
                  <num>(1)</num>
                  <content>
                    <p>Normal subsection:</p>
                    <blockList id="section-303.1.list0">
                      <listIntroduction>Normal list:</listIntroduction>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <p>normal item;</p>
                      </item>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <p>normal item (duplicate number);</p>
                      </item>
                      <item id="section-303.1.list0.a">
                        <num>(a)</num>
                        <blockList id="section-303.1.list0.a.list0">
                          <listIntroduction>normal item (also duplicate):</listIntroduction>
                          <item id="section-303.1.list0.a.list0.i">
                            <num>(i)</num>
                            <blockList id="section-303.1.list0.a.list0.i.list0">
                              <listIntroduction>sublist item, plus:</listIntroduction>
                              <item id="section-303.1.list0.a.list0.i.list0.A">
                                <num>(A)</num>
                                <p>nested further!</p>
                              </item>
                              <item id="section-303.1.list0.a.list0.i.list0.B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                              <item id="section-303.1.list0.a.list0.i.list0.B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                            </blockList>
                          </item>
                          <item id="section-303.1.list0.a.list0.ii">
                            <num>(ii)</num>
                            <p>moar; and</p>
                          </item>
                        </blockList>
                      </item>
                      <item id="section-303.1.list0.b">
                        <num>(b)</num>
                        <p>final item.</p>
                      </item>
                    </blockList>
                  </content>
                </subsection>
                <hcontainer id="section-303.hcontainer_1" name="crossheading">
                  <heading>Let's do this</heading>
                </hcontainer>
              </section>
              <section id="section-304">
                <num>304.</num>
                <heading>Weirdo numbering</heading>
                <subsection id="section-304.304.1">
                  <num>304.1</num>
                  <content>
                    <p>First sub.</p>
                  </content>
                </subsection>
                <subsection id="section-304.304.2">
                  <num>304.2</num>
                  <content>
                    <p>Second sub.</p>
                  </content>
                </subsection>
                <subsection id="section-304.304.3">
                  <num>304.3</num>
                  <content>
                    <p>Third sub.</p>
                  </content>
                </subsection>
              </section>
            </part>
          </mainBody>
        </doc>
      </attachment>
      <attachment id="att_6">
        <heading>Schedule 5</heading>
        <subheading>Wildlife Treaty</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer id="hcontainer_1" name="crossheading">
              <heading>Introduction</heading>
            </hcontainer>
            <hcontainer id="hcontainer_2">
              <content>
                <p>sdfjhasdf;akdjsfnaksdnakdf</p>
              </content>
            </hcontainer>
            <article id="article-1">
              <num>1</num>
              <heading>Wildlife</heading>
              <hcontainer id="article-1.hcontainer_1">
                <content>
                  <p>Introductory text.</p>
                </content>
              </hcontainer>
              <paragraph id="article-1.paragraph-1">
                <num>1.</num>
                <content>
                  <p>sdkfhsdkjbfasdfb</p>
                </content>
              </paragraph>
              <paragraph id="article-1.paragraph-2">
                <num>2.</num>
                <content>
                  <p>sdkfasdkjbfakdjsbf</p>
                </content>
              </paragraph>
              <paragraph id="article-1.paragraph-3">
                <num>3.</num>
                <content>
                  <p>d;khadksjbfdkjbg</p>
                </content>
              </paragraph>
            </article>
            <article id="article-2">
              <num>2</num>
              <heading>Treaty</heading>
              <hcontainer id="article-2.hcontainer_1">
                <content>
                  <p>uygsjdfgjsdhgfsfjhsdjkfhs</p>
                  <p>fljsdhfkahsfkahsdkfhsd</p>
                  <p>sadkjfhksdjhfksdhgkhdf</p>
                  <p>sdfasdfhkadhsfkhakfhsdg</p>
                </content>
              </hcontainer>
            </article>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body/>
    <attachments>
      <attachment eId="att_1">
        <heading>Annexure</heading>
        <subheading>Things to do during lockdown</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Form A</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_2">
              <content>
                <p>I ................. hereby ...............</p>
                <p>Signed</p>
              </content>
            </hcontainer>
            <hcontainer name="crossheading" eId="hcontainer_3">
              <heading>Form B</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_4">
              <content>
                <p>One may:</p>
              </content>
            </hcontainer>
            <paragraph eId="para_1">
              <num>1.</num>
              <content>
                <p>Sing</p>
              </content>
            </paragraph>
            <paragraph eId="para_2">
              <num>2.</num>
              <content>
                <p>Dance</p>
              </content>
            </paragraph>
            <paragraph eId="para_3">
              <num>3.</num>
              <content>
                <p>Sway</p>
              </content>
            </paragraph>
            <hcontainer name="crossheading" eId="hcontainer_5">
              <heading>Form C</heading>
            </hcontainer>
            <section eId="sec_1">
              <num>1.</num>
              <heading>Paragraph heading</heading>
              <subsection eId="sec_1__subsec_1">
                <num>(1)</num>
                <content>
                  <p>sdfkhsdkjfhldfh.</p>
                </content>
              </subsection>
              <subsection eId="sec_1__subsec_2">
                <num>(2)</num>
                <content>
                  <p>sldfhsdkfnldksn.</p>
                </content>
              </subsection>
            </section>
            <section eId="sec_2">
              <num>2.</num>
              <heading>Another heading</heading>
              <subsection eId="sec_2__subsec_1">
                <num>(1)</num>
                <content>
                  <p>dskfahsdkfdnsv.dn.</p>
                </content>
              </subsection>
              <subsection eId="sec_2__subsec_2">
                <num>(2)</num>
                <content>
                  <p>sdfkdskvdnvmbdvmsnd.</p>
                </content>
              </subsection>
            </section>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_2">
        <heading>Schedule 1</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>Column 1</p>
                    </th>
                    <th>
                      <p>Column 2</p>
                    </th>
                    <th>
                      <p>Column 3</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>Sub-Council Designation</p>
                    </th>
                    <th>
                      <p>Sub-Council Name</p>
                    </th>
                    <th>
                      <p>Ward Numbers</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>Subcouncil 1 Blaauwberg</p>
                    </td>
                    <td>
                      <p>4, 23, 29, 32, 104, 107</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>Subcouncil 2 Bergdal</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_3">
        <heading>Schedule 2</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer eId="hcontainer_1">
              <content>
                <table eId="hcontainer_1__table_1">
                  <tr>
                    <th>
                      <p>COLUMN 1</p>
                    </th>
                    <th>
                      <p>COLUMN 2</p>
                    </th>
                  </tr>
                  <tr>
                    <th>
                      <p>SUB-COUNCIL DESIGNATION</p>
                    </th>
                    <th>
                      <p>WARD NUMBERS</p>
                    </th>
                  </tr>
                  <tr>
                    <td>
                      <p>1</p>
                    </td>
                    <td>
                      <p>23, 29, 32 and 104</p>
                    </td>
                  </tr>
                  <tr>
                    <td>
                      <p>2</p>
                    </td>
                    <td>
                      <p>6, 7, 8, 101, 102 and 111</p>
                    </td>
                  </tr>
                </table>
              </content>
            </hcontainer>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_4">
        <heading>Third Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <chapter eId="chp_1">
              <num>1</num>
              <heading>The first Chapter</heading>
              <part eId="chp_1__part_1">
                <num>1</num>
                <heading>The first Part</heading>
                <paragraph eId="chp_1__part_1__para_1">
                  <num>1.</num>
                  <content>
                    <p>The first para</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_1__para_2">
                  <num>2.</num>
                  <content>
                    <p>The second para</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_1__para_345456">
                  <num>345456.</num>
                  <content>
                    <p>The last para</p>
                  </content>
                </paragraph>
              </part>
              <part eId="chp_1__part_2">
                <num>2</num>
                <heading>The second Part</heading>
                <paragraph eId="chp_1__part_2__para_1">
                  <num>1.</num>
                  <content>
                    <p>Starting all over again</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_2__para_2">
                  <num>2.</num>
                  <content>
                    <p>Yup</p>
                  </content>
                </paragraph>
                <paragraph eId="chp_1__part_2__para_3">
                  <num>3.</num>
                  <content>
                    <p>sdflkdsjg;ndfg</p>
                  </content>
                </paragraph>
              </part>
            </chapter>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_5">
        <heading>Fourth Schedule</heading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <part eId="part_36">
              <num>36</num>
              <heading>Let's get nested</heading>
              <chapter eId="part_36__chp_A">
                <num>A</num>
                <heading>Nested Chapter</heading>
                <section eId="sec_1">
                  <num>1.</num>
                  <heading>fjlhsdkfh</heading>
                  <hcontainer eId="sec_1__hcontainer_1">
                    <content>
                      <p>dsjfhsdkjfhkshdf</p>
                    </content>
                  </hcontainer>
                </section>
                <section eId="sec_300">
                  <num>300.</num>
                  <heading>skdfhdkshfasd</heading>
                  <hcontainer eId="sec_300__hcontainer_1">
                    <content>
                      <p>asfjhadjslgfjsdghfjhg</p>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
              <chapter eId="part_36__chp_B">
                <num>B</num>
                <heading>Still inside</heading>
                <section eId="sec_301">
                  <num>301.</num>
                  <heading>skhfdsjghfd</heading>
                  <hcontainer eId="sec_301__hcontainer_1">
                    <content>
                      <p>sdfjsdlgjlkdfjg</p>
                    </content>
                  </hcontainer>
                </section>
                <section eId="sec_302">
                  <num>302.</num>
                  <heading>dkfhdsjhgdbfhjg</heading>
                  <hcontainer eId="sec_302__hcontainer_1">
                    <content>
                      <blockList eId="sec_302__hcontainer_1__list_1">
                        <listIntroduction>And let's nest a list:</listIntroduction>
                        <item eId="sec_302__hcontainer_1__list_1__item_1">
                          <num>(1)</num>
                          <p>These ones are weird:</p>
                          <blockList eId="sec_302__hcontainer_1__list_1__item_1__list_1">
                            <listIntroduction><remark status="editorial">[editorial remark]</remark></listIntroduction>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_a">
                              <num>(a)</num>
                              <p>sfhsdkjfhksdh;</p>
                            </item>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_b">
                              <num>(b)</num>
                              <p>sdfhsdnfbmnsdbf;</p>
                              <p><remark status="editorial">[editorial remark]</remark></p>
                            </item>
                            <item eId="sec_302__hcontainer_1__list_1__item_1__list_1__item_c">
                              <num>(c)</num>
                              <p>jshaasbmnbxc.</p>
                            </item>
                          </blockList>
                        </item>
                        <item eId="sec_302__hcontainer_1__list_1__item_2">
                          <num>(2)</num>
                          <p>A nother not-quite subsection.</p>
                        </item>
                      </blockList>
                    </content>
                  </hcontainer>
                </section>
              </chapter>
            </part>
            <part eId="part_37">
              <num>37</num>
              <heading>Back out to the top level</heading>
              <section eId="sec_303">
                <num>303.</num>
                <heading>sfsjdbfbsdjnfb</heading>
                <subsection eId="sec_303__subsec_1">
                  <num>(1)</num>
                  <content>
                    <p>Normal subsection:</p>
                    <blockList eId="sec_303__subsec_1__list_1">
                      <listIntroduction>Normal list:</listIntroduction>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <p>normal item;</p>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <p>normal item (duplicate number);</p>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_a">
                        <num>(a)</num>
                        <blockList eId="sec_303__subsec_1__list_1__item_a__list_1">
                          <listIntroduction>normal item (also duplicate):</listIntroduction>
                          <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i">
                            <num>(i)</num>
                            <blockList eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1">
                              <listIntroduction>sublist item, plus:</listIntroduction>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_A">
                                <num>(A)</num>
                                <p>nested further!</p>
                              </item>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                              <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_i__list_1__item_B">
                                <num>(B)</num>
                                <p>nested further!</p>
                              </item>
                            </blockList>
                          </item>
                          <item eId="sec_303__subsec_1__list_1__item_a__list_1__item_ii">
                            <num>(ii)</num>
                            <p>moar; and</p>
                          </item>
                        </blockList>
                      </item>
                      <item eId="sec_303__subsec_1__list_1__item_b">
                        <num>(b)</num>
                        <p>final item.</p>
                      </item>
                    </blockList>
                  </content>
                </subsection>
                <hcontainer name="crossheading" eId="sec_303__hcontainer_1">
                  <heading>Let's do this</heading>
                </hcontainer>
              </section>
              <section eId="sec_304">
                <num>304.</num>
                <heading>Weirdo numbering</heading>
                <subsection eId="sec_304__subsec_304-1">
                  <num>304.1</num>
                  <content>
                    <p>First sub.</p>
                  </content>
                </subsection>
                <subsection eId="sec_304__subsec_304-2">
                  <num>304.2</num>
                  <content>
                    <p>Second sub.</p>
                  </content>
                </subsection>
                <subsection eId="sec_304__subsec_304-3">
                  <num>304.3</num>
                  <content>
                    <p>Third sub.</p>
                  </content>
                </subsection>
              </section>
            </part>
          </mainBody>
        </doc>
      </attachment>
      <attachment eId="att_6">
        <heading>Schedule 5</heading>
        <subheading>Wildlife Treaty</subheading>
        <doc name="schedule">
          <meta/>
          <mainBody>
            <hcontainer name="crossheading" eId="hcontainer_1">
              <heading>Introduction</heading>
            </hcontainer>
            <hcontainer eId="hcontainer_2">
              <content>
                <p>sdfjhasdf;akdjsfnaksdnakdf</p>
              </content>
            </hcontainer>
            <article eId="article_1">
              <num>1</num>
              <heading>Wildlife</heading>
              <hcontainer eId="article_1__hcontainer_1">
                <content>
                  <p>Introductory text.</p>
                </content>
              </hcontainer>
              <paragraph eId="article_1__para_1">
                <num>1.</num>
                <content>
                  <p>sdkfhsdkjbfasdfb</p>
                </content>
              </paragraph>
              <paragraph eId="article_1__para_2">
                <num>2.</num>
                <content>
                  <p>sdkfasdkjbfakdjsbf</p>
                </content>
              </paragraph>
              <paragraph eId="article_1__para_3">
                <num>3.</num>
                <content>
                  <p>d;khadksjbfdkjbg</p>
                </content>
              </paragraph>
            </article>
            <article eId="article_2">
              <num>2</num>
              <heading>Treaty</heading>
              <hcontainer eId="article_2__hcontainer_1">
                <content>
                  <p>uygsjdfgjsdhgfsfjhsdjkfhs</p>
                  <p>fljsdhfkahsfkahsdkfhsd</p>
                  <p>sadkjfhksdjhfksdhgkhdf</p>
                  <p>sdfasdfhkadhsfkhakfhsdg</p>
                </content>
              </hcontainer>
            </article>
          </mainBody>
        </doc>
      </attachment>
    </attachments>
  </act>
</akomaNtoso>
""",
            output
        )

    def test_eid_table(self):
        """ includes checks for tables in main body and Schedules
        """
        pass

    def test_href(self):
        """ checks that (only) internal section references are updated
        """
        migration = HrefMigration()
        doc = Document(work=self.work, document_xml="""
<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body>
      <chapter eId="chapter-VIII">
        <num>VIII</num>
        <heading>Emissions from compression ignition powered vehicles</heading>
        <section eId="section-22">
          <num>22.</num>
          <heading>Stopping of vehicles for inspection and testing</heading>
          <subsection eId="section-22.1">
            <num>(1)</num>
            <content>
              <p>In order to enable an <term refersTo="#term-authorised_official" eId="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" eId="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" eId="trm266">vehicle</term>.</p>
            </content>
          </subsection>
          <subsection eId="section-22.2">
            <num>(2)</num>
            <content>
              <blockList eId="section-22.2.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" eId="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" eId="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" eId="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" eId="trm270">vehicle</term> in order to -</listIntroduction>
                <item eId="section-22.2.list0.b">
                  <num>(b)</num>
                  <p>conduct a visual inspection of the <term refersTo="#term-vehicle" eId="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#section-21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#section-23">section 23</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section eId="section-23">
          <num>23.</num>
          <heading>Testing procedure</heading>
          <subsection eId="section-23.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" eId="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" eId="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" eId="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#section-21">section 21</ref>(1).</p>
            </content>
          </subsection>
          <subsection eId="section-23.3">
            <num>(3)</num>
            <content>
              <blockList eId="section-23.3.list0">
                <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" eId="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" eId="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" eId="trm295">vehicle</term> -</listIntroduction>
                <item eId="section-23.3.list0.a">
                  <num>(a)</num>
                  <p>is not emitting <term refersTo="#term-dark_smoke" eId="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" eId="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" eId="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#section-21">section 21</ref>; or</p>
                </item>
                <item eId="section-23.3.list0.b">
                  <num>(b)</num>
                  <p>is emitting <term refersTo="#term-dark_smoke" eId="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" eId="trm300">vehicle</term> with a repair notice in accordance with <ref href="#section-24">section 24</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section eId="section-24">
          <num>24.</num>
          <heading>Repair notice</heading>
          <subsection eId="section-24.1">
            <num>(1)</num>
            <content>
              <p>In the event that a determination is made in terms of <ref href="#section-23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
            </content>
          </subsection>
        </section>
      </chapter>
    </body>
  </act>
</akomaNtoso>""")
        migration.migrate_document(doc)
        output = doc.doc.to_xml(pretty_print=True, encoding='unicode')
        self.assertMultiLineEqual(
            """<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
  <act contains="singleVersion">
    <meta/>
    <body>
      <chapter eId="chapter-VIII">
        <num>VIII</num>
        <heading>Emissions from compression ignition powered vehicles</heading>
        <section eId="section-22">
          <num>22.</num>
          <heading>Stopping of vehicles for inspection and testing</heading>
          <subsection eId="section-22.1">
            <num>(1)</num>
            <content>
              <p>In order to enable an <term refersTo="#term-authorised_official" eId="trm264">authorised official</term> to enforce the provisions of this Chapter, the driver of a <term refersTo="#term-vehicle" eId="trm265">vehicle</term> must comply with any reasonable direction given by an authorised official to conduct or facilitate the inspection or testing of the <term refersTo="#term-vehicle" eId="trm266">vehicle</term>.</p>
            </content>
          </subsection>
          <subsection eId="section-22.2">
            <num>(2)</num>
            <content>
              <blockList eId="section-22.2.list0">
                <listIntroduction>An <term refersTo="#term-authorised_official" eId="trm267">authorised official</term> may issue an instruction to the driver of a <term refersTo="#term-vehicle" eId="trm268">vehicle</term> suspected of emitting <term refersTo="#term-dark_smoke" eId="trm269">dark smoke</term> to stop the <term refersTo="#term-vehicle" eId="trm270">vehicle</term> in order to -</listIntroduction>
                <item eId="section-22.2.list0.b">
                  <num>(b)</num>
                  <p>conduct a visual inspection of the <term refersTo="#term-vehicle" eId="trm274">vehicle</term> and, if the authorised official reasonably believes that an offence has been committed under <ref href="#sec_21">section 21</ref> instruct the driver of the vehicle, who is presumed to be the owner of the vehicle unless he or she produces evidence to the contrary in writing, to take the vehicle to a specified address or testing station, within a specified period of time, for inspection and testing in accordance with <ref href="#sec_23">section 23</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section eId="section-23">
          <num>23.</num>
          <heading>Testing procedure</heading>
          <subsection eId="section-23.1">
            <num>(1)</num>
            <content>
              <p>An <term refersTo="#term-authorised_official" eId="trm275">authorised official</term> must use the <term refersTo="#term-free_acceleration_test" eId="trm276">free acceleration test</term> method in order to determine whether a <term refersTo="#term-compression_ignition_powered_vehicle" eId="trm277">compression ignition powered vehicle</term> is being driven or used in contravention of <ref href="#sec_21">section 21</ref>(1).</p>
            </content>
          </subsection>
          <subsection eId="section-23.3">
            <num>(3)</num>
            <content>
              <blockList eId="section-23.3.list0">
                <listIntroduction>If, having conducted the <term refersTo="#term-free_acceleration_test" eId="trm293">free acceleration test</term>, the <term refersTo="#term-authorised_official" eId="trm294">authorised official</term> is satisfied that the <term refersTo="#term-vehicle" eId="trm295">vehicle</term> -</listIntroduction>
                <item eId="section-23.3.list0.a">
                  <num>(a)</num>
                  <p>is not emitting <term refersTo="#term-dark_smoke" eId="trm296">dark smoke</term>, he or she must furnish the driver of the <term refersTo="#term-vehicle" eId="trm297">vehicle</term> with a certificate indicating that the <term refersTo="#term-vehicle" eId="trm298">vehicle</term> is not being driven or used in contravention of <ref href="#sec_21">section 21</ref>; or</p>
                </item>
                <item eId="section-23.3.list0.b">
                  <num>(b)</num>
                  <p>is emitting <term refersTo="#term-dark_smoke" eId="trm299">dark smoke</term>, he or she must issue the driver of the <term refersTo="#term-vehicle" eId="trm300">vehicle</term> with a repair notice in accordance with <ref href="#sec_24">section 24</ref>.</p>
                </item>
              </blockList>
            </content>
          </subsection>
        </section>
        <section eId="section-24">
          <num>24.</num>
          <heading>Repair notice</heading>
          <subsection eId="section-24.1">
            <num>(1)</num>
            <content>
              <p>In the event that a determination is made in terms of <ref href="#sec_23">section 23</ref>(3) that a vehicle is emitting dark smoke the authorised official must instruct the owner of the vehicle in writing to repair the vehicle and present it for re-testing at the address specified in a repair notice;</p>
            </content>
          </subsection>
        </section>
      </chapter>
    </body>
  </act>
</akomaNtoso>
""",
            output
        )
