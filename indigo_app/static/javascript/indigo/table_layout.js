/* Pure table planning; keep in sync with indigo_api/table_layout.py.
 * Shared fixtures cover both ports. DOM/FOP repairs belong in the adapters.
 */
(function(exports) {
  'use strict';
  exports.Indigo = exports.Indigo || {};
  const MAX_COLUMNS = 10000;
  const MAX_GRID_SLOTS = 1000000;
  const EPSILON = 1e-7;
  class TableLayout {
    constructor(rows, columnWidths = null) {
      this.rows = rows;
      this.columnWidths = columnWidths;
    }

    static fromTable(table) {
      return new this(this.rows(table), this.columnWidths(table));
    }

    static parseSpan(value) {
      if (value === null || value === undefined || value === '') return 1;
      if (typeof value !== 'string' || !/^[0-9]+$/.test(value)) return null;
      value = value.replace(/^0+/, '') || '0';
      if (value.length > 5) return null;
      const number = Number(value);
      return number >= 1 && number <= MAX_COLUMNS ? number : null;
    }
    static percentageWidth(style) {
      // The last width declaration is authoritative, as in CSS.
      const declarations = (style || '').split(';').filter(part => part.includes(':') && part.split(':')[0].trim().toLowerCase() === 'width');
      const value = declarations.length ? declarations[declarations.length - 1].split(':').slice(1).join(':') : '';
      const match = /^\s*((?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?)\s*%\s*$/i.exec(value);
      const number = match ? Number(match[1]) : null;
      return number !== null && Number.isFinite(number) && number <= 100 ? number : null;
    }
    static rows(table) {
      return Array.from(table.children).filter(el => el.localName === 'tr').map(row =>
        Array.from(row.children).filter(el => el.localName === 'td' || el.localName === 'th').map(cell =>
          ({colspan: cell.getAttribute('colspan'), rowspan: cell.getAttribute('rowspan'), style: cell.getAttribute('style') || ''})));
    }
    static columnWidths(table) {
      const groups = Array.from(table.children).filter(el => el.localName === 'colgroup');
      if (!groups.length) return null;
      if (groups.length !== 1) return [];
      const widths = [];
      for (const col of groups[0].children) {
        if (col.localName !== 'col') continue;
        const width = col.attributes.length === 1 && col.hasAttribute('width') ? TableLayout.percentageWidth('width:' + col.getAttribute('width')) : null;
        if (width === null) return [];
        widths.push(width);
      }
      return widths;
    }
    geometry() {
      const rows = this.rows;
      const occupied = rows.map(() => []);
      const cells = [];
      const divisions = new Set([0]);
      let columns = 0;
      for (let y = 0; y < rows.length; y++) {
        let start = 0;
        for (let index = 0; index < rows[y].length; index++) {
          let covering;
          while ((covering = occupied[y].find(range => range[0] <= start && start < range[1]))) start = covering[1];
          const colspan = TableLayout.parseSpan(rows[y][index].colspan);
          const rowspan = TableLayout.parseSpan(rows[y][index].rowspan);
          if (colspan === null || rowspan === null || y + rowspan > rows.length) return null;
          const end = start + colspan;
          if (end > MAX_COLUMNS) return null;
          for (let r = y; r < y + rowspan; r++) {
            if (occupied[r].some(range => start < range[1] && range[0] < end)) return null;
            occupied[r].push([start, end]);
          }
          divisions.add(start);
          divisions.add(end);
          cells.push({row: y, index, start, end, rowspan});
          columns = Math.max(columns, end);
          start = end;
        }
      }
      if (!columns || columns * rows.length > MAX_GRID_SLOTS || occupied.some(row => row.reduce((n, range) => n + range[1] - range[0], 0) !== columns)) return null;
      return {cells, columns, divisions: Array.from(divisions).sort((a, b) => a - b)};
    }
    legacyWidths(layout) {
      const rows = this.rows;
      let widths = Array(layout.columns).fill(0);
      for (const cell of layout.cells) {
        const width = TableLayout.percentageWidth(rows[cell.row][cell.index].style);
        if (cell.end - cell.start === 1 && !widths[cell.start] && width !== null) widths[cell.start] = Math.floor(width);
      }
      let total = widths.reduce((a, b) => a + b, 0);
      let missing = widths.map((w, i) => w ? -1 : i).filter(i => i !== -1);
      if (total > 100 && missing.length) {
        widths = Array(layout.columns).fill(0);
        missing = widths.map((w, i) => i);
        total = 0;
      }
      const fallback = Math.floor((100 - total) / (missing.length || 1));
      missing.forEach(i => { widths[i] = fallback; });
      total = widths.reduce((a, b) => a + b, 0);
      if (total <= 0 || widths.some(w => w <= 0)) return widths.map(() => 100 / widths.length);
      return widths.map(w => w * 100 / total);
    }
    resolveWidths(layout) {
      const rows = this.rows, columnWidths = this.columnWidths;
      const count = layout.columns;
      if (columnWidths !== null) {
        if (columnWidths.length !== count || columnWidths.some(w => typeof w !== 'number' || !Number.isFinite(w) || w <= 0)) return null;
        if (Math.abs(columnWidths.reduce((a, b) => a + b, 0) - 100) > EPSILON) return null;
        return columnWidths.slice();
      }
      const edges = Array.from({length: count + 1}, () => []);
      for (const cell of layout.cells) {
        const width = TableLayout.percentageWidth(rows[cell.row][cell.index].style);
        if (width === null) continue;
        edges[cell.start].push([cell.end, width]);
        edges[cell.end].push([cell.start, -width]);
      }
      let positions = Array(count + 1).fill(null);
      positions[0] = 0;
      const propagate = queue => {
        for (const a of queue) {
          for (const [b, width] of edges[a]) {
            const value = positions[a] + width;
            if (positions[b] === null) { positions[b] = value; queue.push(b); }
            else if (Math.abs(positions[b] - value) > EPSILON) return false;
          }
        }
        return true;
      };
      if (!propagate([0])) return null;
      if (positions[count] !== null) {
        if (positions[count] <= 0) return null;
        const scale = 100 / positions[count];
        positions = positions.map(p => p === null ? null : p * scale);
      } else {
        positions[count] = 100;
        if (!propagate([count])) return null;
      }
      if (edges.some((edge, i) => edge.length && positions[i] === null)) return null;
      const cumulative = [0];
      this.legacyWidths(layout).forEach(w => cumulative.push(cumulative[cumulative.length - 1] + w));
      const known = positions.map((p, i) => p === null ? -1 : i).filter(i => i !== -1);
      for (let n = 1; n < known.length; n++) {
        const left = known[n - 1], right = known[n];
        for (let i = left + 1; i < right; i++) {
          const fraction = (cumulative[i] - cumulative[left]) / (cumulative[right] - cumulative[left]);
          positions[i] = positions[left] + (positions[right] - positions[left]) * fraction;
        }
      }
      const widths = positions.slice(1).map((p, i) => p - positions[i]);
      return widths.every(w => w > 0) ? widths : null;
    }
    static cleanWidth(value) {
      const nearest = Math.floor(value + 0.5);
      return nearest > 0 && Math.abs(value - nearest) < 1e-10 ? nearest : value;
    }
    plan() {
      const layout = this.geometry();
      if (layout === null) return null;
      const widths = this.resolveWidths(layout);
      if (widths === null) return null;
      const positions = new Map(layout.divisions.map((n, i) => [n, i]));
      const cumulative = [0];
      widths.forEach(w => cumulative.push(cumulative[cumulative.length - 1] + w));
      const compactWidths = layout.divisions.slice(1).map((end, i) => TableLayout.cleanWidth(cumulative[end] - cumulative[layout.divisions[i]]));
      layout.cells.forEach(cell => {
        cell.colspan = positions.get(cell.end) - positions.get(cell.start);
        cell.width = TableLayout.cleanWidth(cumulative[cell.end] - cumulative[cell.start]);
      });
      return {...layout, widths, compact_widths: compactWidths};
    }
  }
  exports.Indigo.TableLayout = TableLayout;
})(window);
