# -*- coding: utf-8 -*-

from nose.tools import *  # noqa

from django.test import testcases
from indigo_api.importers.za import ImporterZA


class ImporterZATestCase(testcases.TestCase):
    def setUp(self):
        self.importer = ImporterZA()

    def test_remove_boilerplace(self):
        text = """text
    this gazette is also available in paper

page 2 of 22
-------------
PUBLISHED IN THE PROVINCIAL GAZETTE

22 Augest 2018

more text
"""
        reformatted = self.importer.reformat_text(text)
        assert_equal(reformatted, "text\n\n\n\n\n\nmore text\n")

    def test_break_nested_lists(self):
        assert_equal(self.importer.break_lines(
            'stored, if known; (b) the number of trolleys'),
            "stored, if known;\n(b) the number of trolleys")

        assert_equal(self.importer.break_lines(
            "(5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or\n(b) 30 days after publishing a general"),
            "(5) The officer-in-Charge may –\n(a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or\n(b) 30 days after publishing a general")

        assert_equal(self.importer.break_lines(
            "(2) No person may – (a) plant, cut or remove plants, shrubs or flowers on a grave without the permission of the officer-in-charge; (b) plant, cut or remove plants, shrubs or flowers on the berm section; or"),
            "(2) No person may –\n(a) plant, cut or remove plants, shrubs or flowers on a grave without the permission of the officer-in-charge;\n(b) plant, cut or remove plants, shrubs or flowers on the berm section; or")

        assert_equal(self.importer.break_lines(
            '(b) its successor in title; or (c) a structure or person exercising a delegated power or carrying out an instruction, where any power in these By-laws, has been delegated or sub-delegated or an instruction given as contemplated in, section 59 of the Local Government: Municipal Systems Act, 2000 (Act No. 32 of 2000); or (d) a service provider fulfilling a responsibility under these By-laws, assigned to it in terms of section 81(2) of the Local Government: Municipal Systems Act, 2000, or any other law, as the case may be;'),
            "(b) its successor in title; or\n(c) a structure or person exercising a delegated power or carrying out an instruction, where any power in these By-laws, has been delegated or sub-delegated or an instruction given as contemplated in, section 59 of the Local Government: Municipal Systems Act, 2000 (Act No. 32 of 2000); or\n(d) a service provider fulfilling a responsibility under these By-laws, assigned to it in terms of section 81(2) of the Local Government: Municipal Systems Act, 2000, or any other law, as the case may be;")

    def should_break_at_likely_subsections(self):
        assert_equal(self.importer.break_lines(
            '(c) place a metal cot on any grave. (3) A person may only erect, place or leave, an object or decoration on a grave during the first 30 days following the burial. (4) Natural or artificial flowers contained in receptacles may be placed on a grave at any time, but in a grave within a berm section or with a headstone, such flowers may only be placed in the socket provided. (5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or'),
            "(c) place a metal cot on any grave.\n(3) A person may only erect, place or leave, an object or decoration on a grave during the first 30 days following the burial.\n(4) Natural or artificial flowers contained in receptacles may be placed on a grave at any time, but in a grave within a berm section or with a headstone, such flowers may only be placed in the socket provided.\n(5) The officer-in-Charge may – (a) remove all withered natural flowers, faded or damaged artificial flowers and any receptacle placed on a grave; or")

    def should_break_lines_at_likely_section_titles(self):
        assert_equal(self.importer.break_lines(
            'foo bar. New section title 62. (1) For the purpose'),
            "foo bar.\nNew section title\n62. (1) For the purpose")
        assert_equal(self.importer.break_lines(
            'foo bar. New section title 62.(1) For the purpose'),
            "foo bar.\nNew section title\n62.(1) For the purpose")
        assert_equal(self.importer.break_lines(
            'New section title 62. (1) For the purpose'),
            "New section title\n62. (1) For the purpose")
        assert_equal(self.importer.break_lines(
            'New section title 62.(1) For the purpose'),
            "New section title\n62.(1) For the purpose")

    def should_clean_up_wrapped_definition_lines_after_pdf(self):
        assert_equal(self.importer.break_lines(
            '“agricultural holding” means a portion of land not less than 0.8 hectares in extent used solely or mainly for the purpose of agriculture, horticulture or for breeding or keeping domesticated animals, poultry or bees; “approved” means as approved by the Council; “bund wall” means a containment wall surrounding an above ground storage tank, constructed of an impervious material and designed to contain 110% of the contents of the tank; “certificate of fitness” means a certificate contemplated in section 20; “certificate of registration” means a certificate contemplated in section 35;'),
            "“agricultural holding” means a portion of land not less than 0.8 hectares in extent used solely or mainly for the purpose of agriculture, horticulture or for breeding or keeping domesticated animals, poultry or bees;\n“approved” means as approved by the Council;\n“bund wall” means a containment wall surrounding an above ground storage tank, constructed of an impervious material and designed to contain 110% of the contents of the tank;\n“certificate of fitness” means a certificate contemplated in section 20;\n“certificate of registration” means a certificate contemplated in section 35;")

    def should_break_at_CAPCASE_TO_Normal_Case(self):
        assert_equal(self.importer.break_lines(
            'CHAPTER 3 PARKING METER PARKING GROUNDS Place of parking 7. No person may park or cause or permit to be parked any vehicle or allow a vehicle to be or remain in a parking meter parking ground otherwise than in a parking bay.'),
            "CHAPTER 3 PARKING METER PARKING GROUNDS\nPlace of parking 7. No person may park or cause or permit to be parked any vehicle or allow a vehicle to be or remain in a parking meter parking ground otherwise than in a parking bay.")
