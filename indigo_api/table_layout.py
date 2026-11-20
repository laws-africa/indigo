"""Table layout planning, mirrored by indigo/table_layout.js.

No DOM mutation or FOP repairs belong here. Shared fixtures exercise both ports.
"""
import math
import re


class TableLayout:
    """Plan a table grid and widths without mutating its source DOM.

    Keep the algorithm in sync with the browser TableLayout class.
    """

    MAX_COLUMNS = 10000
    MAX_GRID_SLOTS = 1000000
    EPSILON = 1e-7
    SPAN = re.compile(r'^[0-9]+$')
    WIDTH = re.compile(r'\s*((?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*%\s*', re.I)

    def __init__(self, rows, column_widths=None):
        self.rows = rows
        self.column_widths = column_widths

    @classmethod
    def from_table(cls, table):
        return cls(cls.table_rows(table), cls.table_column_widths(table))

    @staticmethod
    def parse_span(value):
        if value is None or value == '':
            return 1
        if not isinstance(value, str) or not TableLayout.SPAN.fullmatch(value):
            return None
        value = value.lstrip('0') or '0'
        if len(value) > 5:
            return None
        number = int(value)
        return number if 1 <= number <= TableLayout.MAX_COLUMNS else None

    @staticmethod
    def percentage_width(style):
        # The last width declaration is authoritative, as in CSS.
        declarations = [part.split(':', 1)[1] for part in (style or '').split(';')
                        if ':' in part and part.split(':', 1)[0].strip().lower() == 'width']
        match = TableLayout.WIDTH.fullmatch(declarations[-1]) if declarations else None
        number = float(match[1]) if match else None
        return number if number is not None and math.isfinite(number) and number <= 100 else None

    @staticmethod
    def table_rows(table):
        ns = {'a': table.nsmap.get(None) or table.tag.split('}')[0][1:]}
        return [[{'colspan': c.get('colspan'), 'rowspan': c.get('rowspan'), 'style': c.get('style', '')}
                 for c in r.xpath('a:td | a:th', namespaces=ns)]
                for r in table.findall(f'{{{ns["a"]}}}tr')]

    def geometry(self):
        rows = self.rows
        occupied = [[] for _ in rows]
        cells = []
        divisions = {0}
        columns = 0
        for y, row in enumerate(rows):
            start = 0
            for index, cell in enumerate(row):
                while True:
                    covering = next((r for r in occupied[y] if r[0] <= start < r[1]), None)
                    if covering is None:
                        break
                    start = covering[1]
                colspan, rowspan = TableLayout.parse_span(cell.get('colspan')), TableLayout.parse_span(cell.get('rowspan'))
                if colspan is None or rowspan is None or y + rowspan > len(rows):
                    return None
                end = start + colspan
                if end > TableLayout.MAX_COLUMNS:
                    return None
                for r in range(y, y + rowspan):
                    if any(start < right and left < end for left, right in occupied[r]):
                        return None
                    occupied[r].append((start, end))
                divisions.update((start, end))
                cells.append({'row': y, 'index': index, 'start': start, 'end': end, 'rowspan': rowspan})
                columns = max(columns, end)
                start = end
        if not columns or columns * len(rows) > TableLayout.MAX_GRID_SLOTS or any(sum(right - left for left, right in row) != columns for row in occupied):
            return None
        return {'cells': cells, 'columns': columns, 'divisions': sorted(divisions)}

    def legacy_widths(self, layout):
        """Historical width policy, using actual cell positions instead of offsets."""
        rows = self.rows
        widths = [0.0] * layout['columns']
        for cell in layout['cells']:
            width = TableLayout.percentage_width(rows[cell['row']][cell['index']].get('style'))
            if cell['end'] - cell['start'] == 1 and not widths[cell['start']] and width is not None:
                widths[cell['start']] = math.floor(width)
        total = sum(widths)
        missing = [i for i, w in enumerate(widths) if not w]
        if total > 100 and missing:
            widths = [0.0] * len(widths)
            missing = list(range(len(widths)))
            total = 0
        default = math.floor((100 - total) / (len(missing) or 1))
        for i in missing:
            widths[i] = default
        total = sum(widths)
        if total <= 0 or any(w <= 0 for w in widths):
            return [100 / len(widths)] * len(widths)
        return [w * 100 / total for w in widths]

    def resolve_widths(self, layout):
        rows, column_widths = self.rows, self.column_widths
        count = layout['columns']
        if column_widths is not None:
            if len(column_widths) != count or any(type(w) not in (float, int) or not math.isfinite(w) or w <= 0 for w in column_widths):
                return None
            if abs(sum(column_widths) - 100) > TableLayout.EPSILON:
                return None
            return list(column_widths)
        # Complete, consistent cell-width constraints preserve editor-saved grids.
        # Known cell edges constrain the grid; interpolate only unused divisions.
        edges = [[] for _ in range(count + 1)]
        for cell in layout['cells']:
            width = TableLayout.percentage_width(rows[cell['row']][cell['index']].get('style'))
            if width is None:
                continue
            a, b = cell['start'], cell['end']
            edges[a].append((b, width))
            edges[b].append((a, -width))
        positions = [None] * (count + 1)
        positions[0] = 0.0

        def propagate(queue):
            for a in queue:
                for b, width in edges[a]:
                    value = positions[a] + width
                    if positions[b] is None:
                        positions[b] = value
                        queue.append(b)
                    elif abs(positions[b] - value) > TableLayout.EPSILON:
                        return False
            return True

        if not propagate([0]):
            return None
        if positions[-1] is not None:
            if positions[-1] <= 0:
                return None
            scale = 100 / positions[-1]
            positions = [p * scale if p is not None else None for p in positions]
        else:
            positions[-1] = 100.0
            if not propagate([count]):
                return None
        if any(positions[a] is None for a in range(count + 1) if edges[a]):
            return None
        defaults = self.legacy_widths(layout)
        cumulative = [0.0]
        for width in defaults:
            cumulative.append(cumulative[-1] + width)
        known = [i for i, p in enumerate(positions) if p is not None]
        for left, right in zip(known, known[1:]):
            for i in range(left + 1, right):
                fraction = (cumulative[i] - cumulative[left]) / (cumulative[right] - cumulative[left])
                positions[i] = positions[left] + (positions[right] - positions[left]) * fraction
        widths = [b - a for a, b in zip(positions, positions[1:])]
        return widths if all(w > 0 for w in widths) else None

    @staticmethod
    def clean_width(value):
        nearest = math.floor(value + 0.5)
        return float(nearest) if nearest > 0 and abs(value - nearest) < 1e-10 else value

    def plan(self):
        layout = self.geometry()
        if layout is None:
            return None
        widths = self.resolve_widths(layout)
        if widths is None:
            return None
        positions = {division: i for i, division in enumerate(layout['divisions'])}
        cumulative = [0.0]
        for width in widths:
            cumulative.append(cumulative[-1] + width)
        compact_widths = [TableLayout.clean_width(cumulative[b] - cumulative[a]) for a, b in zip(layout['divisions'], layout['divisions'][1:])]
        for cell in layout['cells']:
            cell['colspan'] = positions[cell['end']] - positions[cell['start']]
            cell['width'] = TableLayout.clean_width(cumulative[cell['end']] - cumulative[cell['start']])
        return {**layout, 'widths': widths, 'compact_widths': compact_widths}

    @staticmethod
    def table_column_widths(table):
        ns = table.tag.split('}')[0][1:]
        groups = table.findall(f'{{{ns}}}colgroup')
        if not groups:
            return None
        if len(groups) != 1:
            return []
        result = []
        for col in groups[0].findall(f'{{{ns}}}col'):
            width = col.get('width', '')
            number = TableLayout.percentage_width('width:' + width) if set(col.attrib) == {'width'} else None
            if number is None:
                return []
            result.append(number)
        return result
