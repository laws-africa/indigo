from itertools import izip

import jsonpatch


IGNORE_FIELDS = ('created_at', 'updated_at', 'updated_by_user', 'created_by_user', 'id')


def decorate_versions(versions, ignore=IGNORE_FIELDS):
    # make pretty differences
    for curr, prev in izip(versions, list(versions[1:]) + [None]):
        curr_d = curr.field_dict
        prev_d = {} if prev is None else prev.field_dict

        for fld in ignore:
            for d in [curr_d, prev_d]:
                if fld in d:
                    del d[fld]

        patch = jsonpatch.make_patch(curr_d, prev_d)

        curr.previous = prev
        curr.changes = sorted([{
            'field': p['path'][1:].replace('_', ' '),
            'path': p['path'],
            'old': prev_d.get(p['path'][1:]),
            'new': curr_d.get(p['path'][1:]),
        } for p in patch], key=lambda x: x['field'])

    return versions
