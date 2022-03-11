import subprocess
import re
import tempfile
import os
from shutil import copyfile


def pdf_count_pages(fname):
    """ Counts the number of pages in a PDF.
    """
    result = subprocess.run(["pdfinfo", fname], stdout=subprocess.PIPE, check=True)
    m = re.search(r'^Pages:\s*(\d+)', result.stdout.decode('utf-8', errors='replace'), re.MULTILINE)
    if m:
        return int(m.group(1))
    else:
        raise ValueError("No page count in {}".format(result.stdout))


def pdf_is_encrypted(fname):
    """ Is this pdf encrypted?
    """
    result = subprocess.run(["pdfinfo", fname], stdout=subprocess.PIPE, check=True)
    m = re.search(r'^Encrypted:\s*(\w+)', result.stdout.decode('utf-8', errors='replace'), re.MULTILINE)
    if m:
        return m.group(1).lower() == 'yes'
    else:
        raise ValueError("No Encrypted field in {}".format(result.stdout))


def pdf_decrypt(src_fname, tgt_fname):
    """ Decrypt a PDF, by converting to PS then back to PDF.
    """
    with tempfile.NamedTemporaryFile() as tmp:
        subprocess.run(["pdftops", src_fname, tmp.name], stdout=subprocess.PIPE, check=True)
        subprocess.run(["ps2pdf", tmp.name, tgt_fname], stdout=subprocess.PIPE, check=True)


def pdf_extract_pages(src_fname, pages, tgt_fname):
    """ Extract pages from pdf named src_fname into tgt_fname (which may be the same file).

    The pages parameter is a list of pages, either single page numbers, or (first, last) tuples
    representing page ranges.
    """
    pdf_pages = pdf_count_pages(src_fname)

    # if it's the whole file (a common case), we don't have to do any work
    if pages == [(1, pdf_pages)]:
        if src_fname != tgt_fname:
            copyfile(src_fname, tgt_fname)
        return

    # if the pdf is encrypted, decrypt it first, since pdfunite can't operate on encrypted pdfs
    if pdf_is_encrypted(src_fname):
        tmp = src_fname + "-decrypted.pdf"
        pdf_decrypt(src_fname, tmp)
        src_fname = tmp

    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, 'page-%d.pdf')
        page_nums = []

        # split the pages out
        for num in pages:
            if isinstance(num, tuple):
                from_page, to_page = num
            else:
                from_page = to_page = num
            subprocess.run(["pdfseparate", src_fname, '-f', str(from_page), '-l', str(to_page), fname], check=True)
            page_nums.extend(list(range(from_page, to_page + 1)))

        # ensure unique, and sort
        page_nums = sorted(list(set(page_nums)))

        # join them back together
        args = ["pdfunite"]
        args.extend([os.path.join(tmpdir, f'page-{i}.pdf') for i in page_nums])
        args.append(tgt_fname)
        subprocess.run(args, check=True)
