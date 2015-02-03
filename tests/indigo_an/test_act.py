from unittest import TestCase

from indigo_an.act import Act

class ActTestCase(TestCase):
    def test_empty_act(self):
        a = Act(None)
        self.assertEqual(a.title, "Untitled")
        self.assertIsNotNone(a.meta)
        self.assertIsNotNone(a.body)
