import html
from difflib import SequenceMatcher

import jsonpatch
from indigo_lib.differ import AKNHTMLDiffer


class AttributeDiffer:
    """ Differ that compares attributes and attribute dictionaries.
    """
    html_differ_class = AKNHTMLDiffer

    def __init__(self):
        self.html_differ = self.html_differ_class()

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
            cmp = getattr(self, 'diff_attr_' + attr, cmp)

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
            'html_old': html.escape(x),
            'html_new': html.escape(x),
        } for x in old]

        diff = {
            'attr': attr,
            'title': title,
            'changes': diffs,
            'type': 'list',
            'old': old,
            'new': new,
        }

        # we're going to modify this
        old = list(old)
        remove_offset = 0

        for patch in jsonpatch.make_patch(old, new):
            # eg. "/0"
            index = int(patch['path'].split("/", 1)[1])

            if patch['op'] == 'add':
                v = patch['value']
                diffs.insert(index, {
                    'old': None,
                    'new': v,
                    'html_old': '',
                    'html_new': "<ins>{}</ins>".format(html.escape(v)),
                })
                # add a fake entry to old, because subsequent references will assume it has happened
                old.insert(index, None)
            elif patch['op'] == 'replace':
                old_v = old[index]
                new_v = patch['value']
                html_old, html_new = self.html_diff(old_v, new_v)
                diffs[index] = {
                    'old': old_v,
                    'new': new_v,
                    'html_old': html_old,
                    'html_new': html_new,
                }
            elif patch['op'] == 'remove':
                index += remove_offset
                v = old[index]
                diffs[index] = {
                    'old': v,
                    'new': None,
                    'html_old': "<del>{}</del>".format(html.escape(v)),
                    'html_new': '',
                }
                # subsequent remove operations will need to be offset
                remove_offset += 1

        return diff

    def html_diff(self, old, new):
        """ Diff strings and return a left, right pair with HTML markup
        indicating differences.
        """
        if old is None:
            old = ''
        if new is None:
            new = ''
        old = str(old).replace('\n', ' ')
        new = str(new).replace('\n', ' ')

        left = []
        right = []

        matcher = SequenceMatcher(None, old, new)
        for opcode, a0, a1, b0, b1 in matcher.get_opcodes():
            if opcode == 'equal':
                s = html.escape(matcher.a[a0:a1])
                left.append(s)
                right.append(s)

            elif opcode == 'insert':
                right.append('<ins>{}</ins>'.format(html.escape(matcher.b[b0:b1])))

            elif opcode == 'delete':
                left.append('<del>{}</del>'.format(html.escape(matcher.a[a0:a1])))

            elif opcode == 'replace':
                left.append('<del>{}</del>'.format(html.escape(matcher.a[a0:a1])))
                right.append('<ins>{}</ins>'.format(html.escape(matcher.b[b0:b1])))

        left = ''.join(left)
        right = ''.join(right)

        return left, right
