# -*- coding: utf-8 -*-
import lxml.etree as ET
import os.path

from django.test import TestCase
from django.core.exceptions import ValidationError


class XSLTTestCase(TestCase):
    def setUp(self):
        self.thisdir = os.path.dirname(os.path.realpath(__file__))

    def load_xslt(self, fname):
        fname = os.path.join(self.thisdir, fname)
        return ET.XSLT(ET.parse(fname))

    def check_xslt_to_txt(self, xsltfile, infile, outfile):
        xslt = self.load_xslt('../static/xsl/act_text.xsl')

        with open(os.path.join(self.thisdir, 'xslt_fixtures', infile)) as f:
            inxml = ET.fromstring(f.read())
        actual = str(xslt(inxml))

        with open(os.path.join(self.thisdir, 'xslt_fixtures', outfile)) as f:
            expected = f.read()

        self.assertMultiLineEqual(expected, actual)

    def test_act_text_xsl_general(self):
        # basic comprehensive check
        self.check_xslt_to_txt('../static/xsl/act_text.xsl',
                               'act_text-general-input.xml',
                               'act_text-general-output.txt')

    def test_act_text_escaping(self):
        # escaping
        self.check_xslt_to_txt('../static/xsl/act_text.xsl',
                               'act_text-escaping-input.xml',
                               'act_text-escaping-output.txt')
