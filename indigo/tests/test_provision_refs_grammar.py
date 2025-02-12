import unittest.util

from django.test import TestCase

from indigo.analysis.refs.provisions import ProvisionRef, parse_provision_refs, MainProvisionRef
from indigo.analysis.refs.provision_refs import ParseError


unittest.util._MAX_LENGTH = 999999999


class ProvisionRefsGrammarTest(TestCase):
    maxDiff = None

    def test_single(self):
        result = parse_provision_refs("Section 1")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            )
        ], result.references)
        self.assertEqual(result.end, 9)

        result = parse_provision_refs("paragraph (a)")
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef("(a)", 10, 13)
            )
        ], result.references)

        result = parse_provision_refs("Section 1.2")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1.2", 8, 11)
            )
        ], result.references)

    def test_single_whitespace(self):
        result = parse_provision_refs("Section 1\n")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            )
        ], result.references)
        self.assertEqual(result.end, 9)

        result = parse_provision_refs("paragraph (a)\n")
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef("(a)", 10, 13)
            )
        ], result.references)

    def test_multiple_main_numbers(self):
        result = parse_provision_refs("Section 1, 32 and 33")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            ),
            MainProvisionRef(
                "Section",
                ProvisionRef("32", 11, 13)
            ),
            MainProvisionRef(
                "Section",
                ProvisionRef("33", 18, 20)
            )
        ], result.references)
        self.assertEqual(result.end, 20)

        result = parse_provision_refs("paragraph (a) and subparagraph (c)")
        self.assertEqual([
            MainProvisionRef(
                "paragraph",
                ProvisionRef("(a)", 10, 13)
            ),
            MainProvisionRef(
                "subparagraph",
                ProvisionRef("(c)", 31, 34)
            )
        ], result.references)

    def test_multiple_main(self):
        result = parse_provision_refs("Section 1 and section 2, section 3 and chapter 4")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1", 8, 9)
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("2", 22, 23)
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("3", 33, 34)
            ),
            MainProvisionRef(
                "chapter",
                ProvisionRef("4", 47, 48)
            )
        ], result.references)

    def test_mixed(self):
        result = parse_provision_refs("Section 1.2(1)(a),(c) to (e), (f)(ii) and (2), and (3)(g),(h) and section 32(a)")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1.2", 8, 11, None,
                    ProvisionRef("(1)", 11, 14, None,
                        ProvisionRef("(a)", 14, 17)
                    ),
                ), [
                    ProvisionRef("(c)", 18, 21, "and_or"),
                    ProvisionRef("(e)", 25, 28, "range"),
                    ProvisionRef("(f)", 30, 33, "and_or",
                        ProvisionRef("(ii)", 33, 37),
                    ),
                    ProvisionRef("(2)", 42, 45, "and_or"),
                    ProvisionRef("(3)", 51, 54, "and_or",
                        ProvisionRef("(g)", 54, 57),
                    ),
                    ProvisionRef("(h)", 58, 61, "and_or"),
                ]
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("32", 74, 76, None,
                    ProvisionRef("(a)", 76, 79),
                ),
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_mixed_newlines(self):
        result = parse_provision_refs("Section 1.2(1)(a),\n(c) to (e), (f)(ii)\nand (2), and (3)\n(g),(h)\nand section 32(a)\n")
        self.assertEqual([
            MainProvisionRef(
                "Section",
                ProvisionRef("1.2", 8, 11, None,
                             ProvisionRef("(1)", 11, 14, None,
                                          ProvisionRef("(a)", 14, 17)
                                          ),
                             ), [
                    ProvisionRef("(c)", 19, 22, "and_or"),
                    ProvisionRef("(e)", 26, 29, "range"),
                    ProvisionRef("(f)", 31, 34, "and_or",
                                 ProvisionRef("(ii)", 34, 38),
                                 ),
                    ProvisionRef("(2)", 43, 46, "and_or"),
                    ProvisionRef("(3)", 52, 55, "and_or",
                                 ProvisionRef("(g)", 56, 59),
                                 ),
                    ProvisionRef("(h)", 60, 63, "and_or"),
                ]
            ),
            MainProvisionRef(
                "section",
                ProvisionRef("32", 76, 78, None,
                             ProvisionRef("(a)", 78, 81),
                             ),
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_range(self):
        result = parse_provision_refs("Section 1.2(1) to (3), (ii) — (iii), (g)- (j)")
        self.assertEqual([
            MainProvisionRef(
                'Section',
                ProvisionRef('1.2', 8, 11, None,
                             ProvisionRef('(1)', 11, 14)),
                             [
                                 ProvisionRef('(3)', 18, 21, 'range'),
                                 ProvisionRef('(ii)', 23, 27, 'and_or'),
                                 ProvisionRef('(iii)', 30, 35, 'range'),
                                 ProvisionRef('(g)', 37, 40, 'and_or'),
                                 ProvisionRef('(j)', 42, 45, 'range')
                             ]
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_range_space_before(self):
        result = parse_provision_refs("Section 1.2(1) to (3), (ii) — (iii), (g) -(j)")
        self.assertEqual([
            MainProvisionRef(
                'Section',
                ProvisionRef('1.2', 8, 11, None,
                             ProvisionRef('(1)', 11, 14)),
                             [
                                 ProvisionRef('(3)', 18, 21, 'range'),
                                 ProvisionRef('(ii)', 23, 27, 'and_or'),
                                 ProvisionRef('(iii)', 30, 35, 'range'),
                                 ProvisionRef('(g)', 37, 40, 'and_or'),
                                 ProvisionRef('(j)', 42, 45, 'range')
                             ]
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_range_no_spaces(self):
        result = parse_provision_refs("Section 1.2(1) to (3), (ii) — (iii), (g)-(j)")
        self.assertEqual([
            MainProvisionRef(
                'Section',
                ProvisionRef('1.2', 8, 11, None,
                             ProvisionRef('(1)', 11, 14)),
                             [
                                 ProvisionRef('(3)', 18, 21, 'range'),
                                 ProvisionRef('(ii)', 23, 27, 'and_or'),
                                 ProvisionRef('(iii)', 30, 35, 'range'),
                                 ProvisionRef('(g)', 37, 40, 'and_or'),
                                 ProvisionRef('(j)', 41, 44, 'range')
                             ]
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_mixed_afr(self):
        result = parse_provision_refs("Afdeling 1.2(1)(a),(c) tot (e), (f)(ii) en (2), en (3)(g),(h) en afdelings 32(a)", "afr")
        self.assertEqual([
            MainProvisionRef(
                "Afdeling",
                ProvisionRef("1.2", 9, 12, None,
                    ProvisionRef("(1)", 12, 15, None,
                        ProvisionRef("(a)", 15, 18)
                    ),
                ), [
                    ProvisionRef("(c)", 19, 22, "and_or"),
                    ProvisionRef("(e)", 27, 30, "range"),
                    ProvisionRef("(f)", 32, 35, "and_or",
                        ProvisionRef("(ii)", 35, 39)),
                    ProvisionRef("(2)", 43, 46, "and_or"),
                    ProvisionRef("(3)", 51, 54, "and_or",
                        ProvisionRef("(g)", 54, 57)),
                    ProvisionRef("(h)", 58, 61, "and_or"),
                ]
            ),
            MainProvisionRef(
                "afdelings",
                ProvisionRef("32", 75, 77, None,
                    ProvisionRef("(a)", 77, 80),
                ),
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_simple_fra(self):
        result = parse_provision_refs("chapitre 1", "fra")
        self.assertEqual([
            MainProvisionRef('chapitre', ProvisionRef('1', 9, 10))
        ], result.references)

        result = parse_provision_refs("chapitre 1 et sous-section 2(a)", "fra")
        self.assertEqual([
            MainProvisionRef('chapitre', ProvisionRef('1', 9, 10)),
            MainProvisionRef('sous-section', ProvisionRef('2', 27, 28, None,
                                                          ProvisionRef('(a)', 28, 31)))
        ], result.references)

        result = parse_provision_refs("chapitre 32 de Loi 3 de 1999", "fra")
        self.assertEqual([
            MainProvisionRef('chapitre', ProvisionRef('32', 9, 11)),
        ], result.references)

    def test_mixed_fra(self):
        result = parse_provision_refs("Chapitres 1.2(1)(a),(c) à (e), (f)(ii) et (2), et (3)(g),(h) et chapitre 32(a)", "fra")
        self.assertEqual([
            MainProvisionRef(
                "Chapitres",
                ProvisionRef("1.2", 10, 13, None,
                             ProvisionRef("(1)", 13, 16, None,
                                          ProvisionRef("(a)", 16, 19)
                                          ),
                             ), [
                    ProvisionRef("(c)", 20, 23, "and_or"),
                    ProvisionRef("(e)", 26, 29, "range"),
                    ProvisionRef("(f)", 31, 34, "and_or",
                                 ProvisionRef("(ii)", 34, 38)),
                    ProvisionRef("(2)", 42, 45, "and_or"),
                    ProvisionRef("(3)", 50, 53, "and_or",
                                 ProvisionRef("(g)", 53, 56)),
                    ProvisionRef("(h)", 57, 60, "and_or"),
                ]
            ),
            MainProvisionRef(
                "chapitre",
                ProvisionRef("32", 73, 75, None,
                             ProvisionRef("(a)", 75, 78),
                             ),
            )
        ], result.references)
        self.assertIsNone(result.target)

    def test_multiple_mains(self):
        result = parse_provision_refs("Section 2(1), section 3(b) and section 32(a)")
        self.assertEqual([
            MainProvisionRef('Section', ProvisionRef('2', 8, 9, None, ProvisionRef('(1)', 9, 12))),
            MainProvisionRef('section', ProvisionRef('3', 22, 23, None, ProvisionRef('(b)', 23, 26))),
            MainProvisionRef('section', ProvisionRef('32', 39, 41, None, ProvisionRef('(a)', 41, 44)))
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("Sections 26 and 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 16, 18)),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("Sections 26 and 31.")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 16, 18)),
        ], result.references)
        self.assertIsNone(result.target)

    def test_multiple_mains_range(self):
        result = parse_provision_refs("Sections 26 to 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('31', 15, 17)),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("Sections 26, 27 and 28 to 31")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('26', 9, 11)),
            MainProvisionRef('Sections', ProvisionRef('27', 13, 15)),
            MainProvisionRef('Sections', ProvisionRef('28', 20, 22)),
            MainProvisionRef('Sections', ProvisionRef('31', 26, 28)),
        ], result.references)
        self.assertIsNone(result.target)

    def test_multiple_mains_target(self):
        result = parse_provision_refs("Sections 2(1), section 3(b) and section 32(a) of another Act")
        self.assertEqual([
            MainProvisionRef('Sections', ProvisionRef('2', 9, 10, None, ProvisionRef('(1)', 10, 13))),
            MainProvisionRef('section', ProvisionRef('3', 23, 24, None, ProvisionRef('(b)', 24, 27))),
            MainProvisionRef('section', ProvisionRef('32', 40, 42, None, ProvisionRef('(a)', 42, 45)))
        ], result.references)
        self.assertEqual("of", result.target)
        self.assertEqual(result.end, 49)

    def test_schedules_num(self):
        result = parse_provision_refs("Schedule 2a")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule 2a", 0, 11)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("schedule 2a.")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule 2a", 0, 11)
            ),
        ], result.references)
        self.assertIsNone(result.target)

    def test_schedules_num_range(self):
        result = parse_provision_refs("schedule 2 to 30")
        self.assertEqual([
            MainProvisionRef('attachment', ProvisionRef('Schedule 2', 0, 10)),
            MainProvisionRef('attachment', ProvisionRef('Schedule 30', 14, 16, separator='range')),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("Schedules 2 and 30")
        self.assertEqual([
            MainProvisionRef('attachment', ProvisionRef('Schedule 2', 0, 11)),
            MainProvisionRef('attachment', ProvisionRef('Schedule 30', 16, 18, separator='and_or')),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("Schedules 10, 11 and 12")
        self.assertEqual([
            MainProvisionRef('attachment', ProvisionRef('Schedule 10', 0, 12)),
            MainProvisionRef('attachment', ProvisionRef('Schedule 11', 14, 16, separator='and_or')),
            MainProvisionRef('attachment', ProvisionRef('Schedule 12', 21, 23, separator='and_or')),
        ], result.references)
        self.assertIsNone(result.target)

    def test_schedules_the_eng(self):
        result = parse_provision_refs("the Schedule")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule", 4, 12)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("the Schedule.")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule", 4, 12)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("the Schedule and also")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Schedule", 4, 12)
            ),
        ], result.references)
        self.assertIsNone(result.target)

    def test_schedules_the_afr(self):
        result = parse_provision_refs("die Bylaag", "afr")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Bylaag", 4, 10)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("die Bylaag.", "afr")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Bylaag", 4, 10)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("die Bylaag en ook", "afr")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("Bylaag", 4, 10)
            ),
        ], result.references)
        self.assertIsNone(result.target)

    def test_schedules_the_fra(self):
        result = parse_provision_refs("l'annexe", "fra")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("l'annexe", 0, 8)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("l'annexe.", "fra")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("l'annexe", 0, 8)
            ),
        ], result.references)
        self.assertIsNone(result.target)

        result = parse_provision_refs("l'annexe et aussi", "fra")
        self.assertEqual([
            MainProvisionRef(
                "attachment",
                ProvisionRef("l'annexe", 0, 8)
            ),
        ], result.references)
        self.assertIsNone(result.target)

    def test_schedules_no_match(self):
        # these must not match as schedule references
        for s in ["the Scheduled work", "the Schedules are also"]:
            with self.assertRaises(ParseError):
                result = parse_provision_refs(s)

    def test_target(self):
        result = parse_provision_refs("Section 2 of this Act")
        self.assertEqual("this", result.target)
        self.assertEqual(result.end, 18)

        result = parse_provision_refs("Section 2, of this Act")
        self.assertEqual("this", result.target)
        self.assertEqual(result.end, 19)

        result = parse_provision_refs("Section 2 thereof")
        self.assertEqual("thereof", result.target)
        self.assertEqual(result.end, 17)

        result = parse_provision_refs("Section 2, thereof and some")
        self.assertEqual("thereof", result.target)
        self.assertEqual(result.end, 18)

        result = parse_provision_refs("Section 2 of the Act")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 20)

        result = parse_provision_refs("Section 2, of the Act with junk")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 21)

        result = parse_provision_refs("Section 2,\nof the Act with junk")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 21)

        result = parse_provision_refs("Section 2\nof the Act with junk")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 20)

    def test_target_truncated(self):
        # the remainder of the text is wrapped in another tag
        result = parse_provision_refs("section 26(a) of ")
        self.assertEqual("of", result.target)
        self.assertEqual(result.end, 17)

    def test_target_afr(self):
        result = parse_provision_refs("Afdeling 2 van hierdie Wet", "afr")
        self.assertEqual("this", result.target)
        self.assertEqual(result.end, 23)

        result = parse_provision_refs("Afdeling 2 daarvan", "afr")
        self.assertEqual("thereof", result.target)
        self.assertEqual(result.end, 18)

        result = parse_provision_refs("Afdeling 2 van die Wet met kak", "afr")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 22)

    def test_target_fra(self):
        result = parse_provision_refs("Section 2 de cette loi", "fra")
        self.assertEqual("this", result.target)
        self.assertEqual(result.end, 19)

        result = parse_provision_refs("Section 2 de ce reglement", "fra")
        self.assertEqual("this", result.target)
        self.assertEqual(result.end, 16)

        result = parse_provision_refs("Section 2 de cela", "fra")
        self.assertEqual("thereof", result.target)
        self.assertEqual(result.end, 17)

        result = parse_provision_refs("Section 2 de la loi mais", "fra")
        self.assertEqual("the_act", result.target)
        self.assertEqual(result.end, 19)
