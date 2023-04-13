import logging
import os.path
import re
import subprocess

from django.conf import settings

log = logging.getLogger(__name__)

FOP_CMD = settings.FOP_CMD
FOP_CONFIG = settings.FOP_CONFIG
FOP_FONT_PATH = settings.FOP_FONT_PATH


def default_fop_config():
    """ Get the full path to the default fop config file, indigo_api/fop.xconf.
        Edit the file by replacing __FONT_PATH__ with the full path to the fonts folder.
        The fonts folder can be given in settings, or the default indigo_api/fonts will be used.
        :return the full path to the (edited) default fop config file.
    """
    fop_config = os.path.join(os.path.dirname(__file__), 'fop.xconf')
    font_path = FOP_FONT_PATH or os.path.join(os.path.dirname(__file__), 'fonts')
    with open(fop_config, 'r+') as f:
        out = re.sub('__FONT_PATH__', font_path, f.read())
        f.truncate()
        f.write(out)
    return fop_config


def run_fop(outf_name, cwd, xml=None, xsl_fo=None, xml_fo=None, output_fo=False):
    """ Run Apache FOP to generate a PDF.

    :param outf_name: filename to write the output to
    :param cwd: working directory to run the command in
    :param xml: filename of raw XML (must be paired with xsl_fo)
    :param xsl_fo: filename of XSL to convert XML to XML-FO (must be paired with xml)
    :param xml_fo: filename of XML-FO file (do not use with xml and xsl_fo)
    :param output_fo: should the output be the FO XML?
    """
    args = [FOP_CMD]
    fop_config_file = FOP_CONFIG or default_fop_config()

    if output_fo:
        # output XML FO, rather than pdf
        args.extend(['-foout', outf_name])
    else:
        args.extend(['-pdf', outf_name])

    args.extend(['-c', fop_config_file])

    if xml_fo:
        # xml fo, no stylesheet
        args.extend(['-fo', xml_fo])
    else:
        # xml and matching xsl to convert to fo
        args.extend(['-xsl', xsl_fo, '-xml', xml])

    log.info(f"Running command in {cwd}: {args}")

    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, cwd=cwd,
                                encoding='utf-8', errors='backslashreplace')
        log.info(f"Output from fop: {result.stdout}")
    except subprocess.CalledProcessError as e:
        log.error(f"Error calling fop. Output: \n{e.output}", exc_info=e)
        raise
