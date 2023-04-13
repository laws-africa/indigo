import logging
import subprocess

from django.conf import settings


log = logging.getLogger(__name__)

FOP_CMD = settings.FOP_CMD
FOP_CONFIG = settings.FOP_CONFIG


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
    if output_fo:
        # output XML FO, rather than pdf
        args.extend(['-foout', outf_name])
    else:
        args.extend(['-pdf', outf_name])

    if FOP_CONFIG:
        args.extend(['-c', FOP_CONFIG])

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
