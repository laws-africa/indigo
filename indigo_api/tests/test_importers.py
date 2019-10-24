from django.test import TestCase


from indigo_api.importers.base import parse_page_nums


class ImporterTestCase(TestCase):
    def test_parse_page_nums_good(self):
        self.assertEqual(parse_page_nums("1"), [1])
        self.assertEqual(parse_page_nums("1-3"), [(1, 3)])
        self.assertEqual(parse_page_nums("1 -3 "), [(1, 3)])
        self.assertEqual(parse_page_nums(" 1, 1 -3, 99  "), [1, (1, 3), 99])

    def test_parse_page_nums_bad(self):
        with self.assertRaises(ValueError):
            parse_page_nums(" -1,  ")
        with self.assertRaises(ValueError):
            parse_page_nums(" a  ")
        with self.assertRaises(ValueError):
            parse_page_nums(" 1-  ")

        self.assertEqual(parse_page_nums(" , ,  "), [])
