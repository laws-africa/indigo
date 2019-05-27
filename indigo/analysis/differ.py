from __future__ import unicode_literals

import cgi
import re
from difflib import Differ, SequenceMatcher
from itertools import izip_longest
from copy import deepcopy
import logging

import jsonpatch
import lxml.html
import lxml.html.builder

log = logging.getLogger(__name__)


def fragments_fromstring(html):
    """ Same as lxml.html.fragments_fromstring, except we preserve initial whitespace.
    """
    items = lxml.html.fragments_fromstring(html)
    match = re.match(r'^(\s+)<', html)
    if match:
        items.insert(0, match.group(1))
    return items


def wrap_tail(elem, wrapper):
    x = wrapper(elem.tail)
    elem.tail = None
    elem.addnext(x)


class AttributeDiffer(object):
    differ = Differ()

    def attr_title(self, attr):
        return attr.title().replace('_', ' ')

    def describe_differences(self, old_dict, new_dict, attrs):
        """ Describe differences in the listed attributes between old_dict and new_dict.

        Returns a list of difference dicts:

            attr: attr being compared
            title: attr in friendly title form
            type: 'str' or 'list'

        If type is 'str':
            old: old value
            new: new value
            html_old: old value as marked-up HTML
            html_new: new value as marked-up HTML

        If type is 'list':
            changes: list of changes as above, for 'str'

        """
        diffs = []

        for attr in attrs:
            title = self.attr_title(attr)
            old = old_dict.get(attr)
            new = new_dict.get(attr)

            cmp = self.diff_default
            if isinstance(old, list) or isinstance(new, list):
                cmp = self.diff_lists
            cmp = getattr(self, 'diff_' + attr, cmp)

            diff = cmp(attr, title, old, new)
            if diff:
                diffs.append(diff)

        return diffs

    def diff_default(self, attr, title, old, new):
        if old != new:
            left, right = self.html_diff(old, new)
            return {
                'attr': attr,
                'title': title,
                'type': 'str',
                'old': old,
                'new': new,
                'html_old': left,
                'html_new': right,
            }

    def diff_lists(self, attr, title, old, new):
        old = old or []
        new = new or []
        if old == new:
            return

        diffs = [{
            'html_old': cgi.escape(x),
            'html_new': cgi.escape(x),
        } for x in old]

        for patch in jsonpatch.make_patch(old, new):
            # eg. "/0"
            index = int(patch['path'].split("/", 1)[1])

            if patch['op'] == 'add':
                v = patch['value']
                diffs.insert(index, {
                    'old': None,
                    'new': v,
                    'html_old': '',
                    'html_new': "<ins>{}</ins>".format(cgi.escape(v)),
                })
            elif patch['op'] == 'replace':
                old_v = old[index]
                new_v = patch['value']
                html_old, html_new = self.html_diff(old_v, new_v)
                diffs.insert(index, {
                    'old': old_v,
                    'new': new_v,
                    'html_old': html_old,
                    'html_new': html_new,
                })
            elif patch['op'] == 'remove':
                v = old[index]
                diffs.insert(index, {
                    'old': v,
                    'new': None,
                    'html_old': "<del>{}</del>".format(cgi.escape(v)),
                    'html_new': '',
                })

        return {
            'attr': attr,
            'title': title,
            'changes': diffs,
            'type': 'list',
        }

    def html_diff(self, old, new):
        """ Diff strings and return a left, right pair with HTML markup
        indicating differences.
        """
        if old is None:
            old = ''
        if new is None:
            new = ''
        old = unicode(old).replace('\n', ' ')
        new = unicode(new).replace('\n', ' ')

        left = []
        right = []

        # TODO: rewrite this using sequermatcher, it's easier

        for diff in self.differ.compare(old, new):
            # diff is a string and one of:
            #   '  x' = 'x' is the same on both sides
            #   '- x' = 'x' has been removed
            #   '+ x' = 'x' has been added
            ch = cgi.escape(diff[2])

            if diff[0] == '+':
                right.append('<ins>{}</ins>'.format(ch))
            elif diff[0] == '-':
                left.append('<del>{}</del>'.format(ch))
            else:
                left.append(ch)
                right.append(ch)

        left = ''.join(left)
        right = ''.join(right)

        return left, right

    def html_inline_diff(self, old, new):
        """ Diff strings and return an inline, unified HTML markup indicating
        differences. """
        if old is None:
            old = ''
        if new is None:
            new = ''

        output = []

        matcher = SequenceMatcher(None, old, new)
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == 'equal':
                output.append(matcher.a[a0:a1])

            elif opcode == 'insert':
                output.append('<ins>{}</ins>'.format(matcher.b[b0:b1]))

            elif opcode == 'delete':
                output.append('<del>{}</del>'.format(matcher.a[a0:a1]))

            elif opcode == 'replace':
                output.append('<del>{}</del>'.format(matcher.a[a0:a1]))
                output.append('<ins>{}</ins>'.format(matcher.b[b0:b1]))

        return ''.join(output)

    def diff_document_html(self, old_tree, new_tree):
        changes = 0

        if old_tree is None:
            new_tree.classes.add('ins')
            changes = 1
        else:
            for diff in self.describe_html_differences(old_tree, new_tree, None):
                changes += 1

                if diff[0] == 'added':
                    log.debug("ADDED: %s", diff[1].tag)
                    new = diff[1]

                    new.classes.add('ins')
                    if new.tail:
                        wrap_tail(new, lxml.html.builder.INS)

                elif diff[0] == 'replaced':
                    log.debug("REPLACED: %s -> %s", diff[1].tag, diff[2].tag)
                    old, new = diff[1], diff[2]

                    old = deepcopy(old)
                    old.classes.add('del')

                    # same as new.addprevious(old) but preserves tails
                    # see https://stackoverflow.com/questions/23282241/
                    new.getparent().insert(new.getparent().index(new), old)
                    if old.tail:
                        wrap_tail(old, lxml.html.builder.DEL)

                    new.classes.add('ins')
                    if new.tail:
                        wrap_tail(new, lxml.html.builder.INS)

                elif diff[0] == 'deleted':
                    log.debug("DELETED: %s", diff[1].tag)
                    old, parent = diff[1:]

                    old = deepcopy(old)
                    old.classes.add('del')

                    # the only possible way that a node can be deleted
                    # if it was the last node in the tree, otherwise
                    # it's considered replaced
                    parent.append(old)
                    if old.tail:
                        wrap_tail(old, lxml.html.builder.DEL)

                elif diff[0] == 'text-differs':
                    log.debug("TEXT CHANGED: %s: %s / %s", diff[1].tag, diff[1].text, diff[2].text)
                    old, new = diff[1], diff[2]

                    html_diff = self.html_inline_diff(old.text, new.text)
                    new.text = None
                    for item in reversed(fragments_fromstring(html_diff)):
                        if isinstance(item, basestring):
                            new.text = item
                        else:
                            new.insert(0, item)

                elif diff[0] == 'tail-differs':
                    log.debug("TAIL CHANGED: %s: %s / %s", diff[1].tag, diff[1].tail, diff[2].tail)
                    old, new = diff[1], diff[2]

                    html_diff = self.html_inline_diff(old.tail, new.tail)
                    prev = new
                    prev.tail = None
                    for item in fragments_fromstring(html_diff):
                        if isinstance(item, basestring):
                            prev.tail = item
                        else:
                            # same as prev.addnext, but preserves prev's tail
                            # see https://stackoverflow.com/questions/23282241/
                            prev.getparent().insert(prev.getparent().index(prev) + 1, item)
                            prev = item

        return changes

    def describe_html_differences(self, old, new, parent):
        if old is None:
            # node entirely new
            yield ('added', new)
            return

        if new is None:
            # node was deleted
            yield ('deleted', old, parent)
            return

        # did the tag change?
        if old.tag != new.tag or old.classes != new.classes:
            yield ('replaced', old, new)
            return

        # TODO diff attributes

        # get a snapshot of the 'new' children, because yielding differences
        # will change the 'new' tree
        kiddies = izip_longest(old.getchildren(), new.getchildren())

        if old.text != new.text and (old.text or '').strip() != (new.text or '').strip():
            yield ('text-differs', old, new)

        if old.tail != new.tail and (old.tail or '').strip() != (new.tail or '').strip():
            yield ('tail-differs', old, new)

        for pair in kiddies:
            for diff in self.describe_html_differences(pair[0], pair[1], new):
                yield diff
