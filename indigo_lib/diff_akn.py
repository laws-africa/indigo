import sys

from lxml import etree

from .differ import AKNHTMLDiffer
from indigo.xmlutils import parse_html_str


def do_diff(html_one, html_two):
    tree_one = parse_html_str(html_one)
    tree_two = parse_html_str(html_two)
    differ = AKNHTMLDiffer()
    diff = differ.diff_html(tree_one, tree_two)
    return etree.tostring(diff, encoding='unicode')


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write(
            "Diffs two AKN HTML files and prints the diff to stdout.\n"
            "Usage: python -m indigo_lib.diff_akn <file1.html> <file2.html>\n"
        )
        sys.exit(1)

    with open(sys.argv[1], "rt") as f:
        html_one = f.read()

    with open(sys.argv[2], "rt") as f:
        html_two = f.read()

    print(do_diff(html_one, html_two))
