function TableEditor(table) {
  var self = this;

  self.onCellChanged = function() {};

  self.setTable = function(table) {
    if (self.$table) {
      self.detach();
    }

    if (!table) {
      self.table = null;
      self.$table = null;
      return;
    }

    self.table = table;
    self.$table = $(table);
    self.attach();
    self.mapTable();
  };

  self.attach = function() {
    // make cells editable
    self.$table.find('td, th').attr('contenteditable', 'true');

    // event handlers
    self.$table.on('focus', 'td, th', self.cellFocused);
    self.$table.on('mouseover', 'td, th', self.overCell);
    self.$table.on('mousedown', 'td, th', self.mouseDown);
    self.$table.on('mouseup', 'td, th', self.mouseUp);
  };

  self.detach = function() {
    // detach events
    self.$table.off('focus', 'td, th', self.cellFocused);
    self.$table.off('mouseover', 'td, th', self.overCell);
    self.$table.off('mousedown', 'td, th', self.mouseDown);
    self.$table.off('mouseup', 'td, th', self.mouseUp);

    // make cells un-editable
    self.$table.find('td, th').removeAttr('contenteditable');
  };

  self.mapTable = function() {
    // calculate the (x, y) coordinates for all cells
    // in the table, taking rowspan and colspan into
    // account.
    // http://stackoverflow.com/questions/13407348/table-cellindex-and-rowindex-with-colspan-rowspan

    var m = [];
    self.cells = [];

    for(var y = 0; y < self.table.rows.length; y++) {
        var row = self.table.rows[y];

        for(var x = 0; x < row.cells.length; x++) {
            var cell = row.cells[x], xx = x, tx, ty;

            // skip already occupied cells in current row
            for (; m[y] && m[y][xx]; ++xx);

            // mark matrix elements occupied by current cell with true
            for (tx = xx; tx < xx + cell.colSpan; ++tx) {
                for (ty = y; ty < y + cell.rowSpan; ++ty) {
                    // fill missing rows
                    if (!m[ty]) m[ty] = [];
                    m[ty][tx] = true;
                }
            }

            if (!self.cells[xx]) self.cells[xx] = [];
            self.cells[xx][y] = cell;
            cell.coords = [xx, y];
        }
    }
  };

  // insert a new row, with +index+ as the index of the new row
  self.insertRow = function(index) {
    var top = self.table.rows[0],
        row = self.table.insertRow(index),
        width = 0;

    // insert the appropriate number of cells for the row, based on the number
    // of cells in the top row
    for (var i = 0; i < top.cells.length; i++) {
      width += top.cells[i].colSpan;
    }

    if (index === 0) {
      // first row, just add cells
      for (i = 0; i < width; i++) {
        row.insertCell().contentEditable = 'true';
      }

    } else {
      // not the first row, need to take colspan and rowspan into account

      for (var x = 0; x < width; x++) {
        var above = self.findCell(x, index-1);

        // only insert a cell if the above cell doesn't span this one
        if (above.coords[1] + above.rowSpan <= index) {
          // doesn't span, add the cell
          row.insertCell().contentEditable = 'true';
        } else {
          // it does span this row
          above.rowSpan += 1;
          x += above.colSpan - 1;
        }
      }
    }

    self.mapTable();

    return row;
  };

  // insert a new column, with +index+ as the index of the new column
  self.insertColumn = function(index) {
    var rows = self.table.rows,
        height = rows.length;

    if (index === 0) {
      // first column, just add cells
      for (i = 0; i < height; i++) {
        rows[i].insertCell(0).contentEditable = 'true';
      }

    } else {
      // not the first column, need to take colspan and rowspan into account

      for (var y = 0; y < height; y++) {
        var left = self.findCell(index-1, y);

        // only insert a cell if another cell doesn't span this one
        if (left.coords[0] + left.colSpan <= index) {
          // doesn't span, append the cell to the closest one in this row
          left = null;
          for (i = index-1; !left && i >= 0; i--) {
            left = self.cells[i] && self.cells[i][y];
          }

          if (left) {
            var newCell = document.createElement(left.tagName);
            newCell.contentEditable = 'true';
            left.insertAdjacentElement('afterend', newCell);
          } else {
            rows[y].insertCell(0).contentEditable = 'true';
          }
        } else {
          // it does span this column
          left.colSpan += 1;
          y += left.rowSpan - 1;
        }
      }
    }

    self.mapTable();
  };

  self.removeColumn = function(index) {
    var cell;

    // unmerge any spanning cells that start in this column
    for (var y = 0; y < self.table.rows.length; y++) {
      cell = self.cells[index] && self.cells[index][y];

      if (cell && (cell.colSpan > 1 || cell.rowSpan > 1)) {
        self.splitCells(index, y, index, y);
      }
    }

    for (y = 0; y < self.table.rows.length; y++) {
      cell = self.cells[index] && self.cells[index][y];

      if (cell) {
        cell.remove();
      } else {
        cell = self.findCell(index, y);
        cell.colSpan -= 1;
        y += cell.rowSpan - 1;
      }
    }

    self.mapTable();
  };

  self.removeRow = function(index) {
    var cell,
        row = self.table.rows[index],
        width = self.table.rows[0].cells.length;

    // unmerge any spanning cells that start in this row
    for (var x = 0; x < row.cells.length; x++) {
      cell = row.cells[x];
      if (cell.colSpan > 1 || cell.rowSpan > 1) {
        self.splitCells(x, index, x, index);
      }
    }

    for (x = 0; x < width; x++) {
      cell = self.cells[x] && self.cells[x][index];

      if (cell) {
        cell.remove();
      } else {
        cell = self.findCell(x, index);
        cell.rowSpan -= 1;
        x += cell.colSpan - 1;
      }
    }

    row.remove();

    self.mapTable();
  };

  self.renameNode = function(node, newname) {
    var newnode = node.ownerDocument.createElement(newname),
        attrs = node.attributes,
        kids = node.childNodes;

    for (var i = 0; i < attrs.length; i++) {
      newnode.setAttribute(attrs[i].name, attrs[i].value);
    }

    while (node.childNodes.length > 0) {
      newnode.appendChild(node.childNodes[0]);
    }

    return newnode;
  };

  self.toggleHeading = function() {
    if (!self.activeCell) return;

    var cell = self.renameNode(self.activeCell, self.activeCell.tagName == 'TH' ? 'td' : 'th');
    self.activeCell.parentElement.replaceChild(cell, self.activeCell);
    self.mapTable();
    self.activeCell = cell;

    cell.focus();
  };

  self.setSelection = function(x1, y1, x2, y2) {
    x2 = x2 === null ? x1 : x2;
    y2 = y2 === null ? y2 : y2;

    /* selection is always:
     *
     * x1, y1 
     *    .------+
     *    |      |
     *    |      |
     *    +------. x2, y2
     */

    // x1, y1, x2, y2
    self.selection = [
      Math.min(x1, x2),
      Math.min(y1, y2),
      Math.max(x1, x2),
      Math.max(y1, y2),
    ];

    self.highlightSelection();
  };

  self.highlightSelection = function() {
    self.$table.find('.selected').removeClass('selected');
    $(self.getCellRange.apply(self, self.selection)).addClass('selected');
  };

  self.getCellRange = function(x1, y1, x2, y2) {
    var cells = [];

    for (var y = y1; y <= y2; y++) {
      for (var x = x1; x <= x2; x++) {
        if (self.cells[x][y]) cells.push(self.cells[x][y]);
      }
    }

    return cells;
  };

  // Find the cell that spans coordinates (x, y)
  self.findCell = function(x, y) {
    var cell = self.cells[x] && self.cells[x][y];
    if (cell) return cell;

    // hunt up
    for (var yy = y - 1; yy >= 0; yy--) {
      cell = self.cells[x] && self.cells[x][yy];
      if (cell) {
        if (yy + cell.rowSpan > y) return cell;
        break;
      }
    }

    // hunt left
    for (var xx = x - 1; xx >= 0; xx--) {
      cell = self.cells[xx] && self.cells[xx][y];
      if (cell) {
       if (xx + cell.colSpan > x) return cell;
       break;
      }
    }

    cell = self.findCell(x-1, y-1);
    if (cell && cell.coords[0] + cell.colSpan > x && cell.coords[1] + cell.rowSpan > y)
      return cell;

    return null;
  };

  self.mergeSelection = function() {
    var x = self.selection[0],
        y = self.selection[1];

    self.mergeCells.apply(self, self.selection);
    self.cells[x][y].focus();
  };

  self.splitSelection = function() {
    var x = self.selection[0],
        y = self.selection[1],
        selection = self.selection;

    self.splitCells.apply(self, self.selection);
    self.cells[x][y].focus();
    self.setSelection.apply(self, selection);
  };

  self.mergeCells = function(x1, y1, x2, y2) {
    var rows = y2 - y1 + 1,
        cols = x2 - x1 + 1;

    if (rows == 1 && cells == 1) return;

    // check and warn about losing text
    var cells = self.getCellRange(x1, y1, x2, y2);
    for (var i = 1; i < cells.length; i++) {
      if (cells[i].innerText) {
        if (!confirm("This will lose some text in the table. Go ahead anyway?")) {
          return false;
        }
        break;
      }
    }

    // first, split any merged cells
    if (self.splitCells(x1, y1, x2, y2)) {
      // refetch the range, since the splitting might have changed things
      cells = self.getCellRange(x1, y1, x2, y2);
    }

    if (cols > 1) cells[0].colSpan = cols;
    if (rows > 1) cells[0].rowSpan = rows;

    // remove the unnecessary cells
    for (i = 1; i < cells.length; ) {
      var span = cells[i].colSpan;
      cells[i].remove();
      i += span;
    }

    self.mapTable();
  };

  self.splitCells = function(x1, y1, x2, y2) {
    var cells = self.getCellRange(x1, y1, x2, y2),
        split = false;

    function appendCells(cell, cols) {
      for (var c = 0; c < cols; c++) {
        var newCell = document.createElement(cell.tagName);
        newCell.contentEditable = 'true';
        cell.insertAdjacentElement('afterend', newCell);
      }
    }

    for (var i = 0; i < cells.length; i++) {
      var cell = cells[i],
          x = cell.coords[0],
          y = cell.coords[1];

      // only split each cell if it needs to be
      if (cell.colSpan > 1 || cell.rowSpan > 1) {
        var colspan = cell.colSpan,
            rowspan = cell.rowSpan;

        split = true;

        // to split a cell, we:
        // 1. remove the span attributes from this, making it normal
        cell.removeAttribute('colspan');
        cell.removeAttribute('rowspan');

        // 2. for each spanned row, find the closest cell to the left of this cell, and append
        //    the necessary number cells to make up the previously spanned columns
        appendCells(cell, colspan-1);

        for (var row = y+1; row < y+rowspan; row++) {
          var col = x,
              cols = colspan,
              rowElem = self.table.rows[row];

          // find the closest cell on the left of the (previously-spanned) cell at [col, row]
          cell = null;
          while (!cell) {
            cell = self.cells[col] && self.cells[col--][row];

            if (!cell && col < 0) {
              cell = rowElem.insertCell(0);
              cell.contentEditable = 'true';
              cols--;
            }
          }

          appendCells(cell, cols);
        }
      }
    }

    if (split) self.mapTable();

    return split;
  };

  /** Event handlers **/

  self.cellFocused = function(e) {
    if (e.target.tagName == 'TH' || e.target.tagName === 'TD') {
      if (self.activeCell != e.target) {
        self.activeCell = e.target;
        self.activeCoords = self.activeCell.coords;
        self.setSelection.apply(self, self.activeCoords);

        self.onCellChanged();
      }
    }
  };

  self.overCell = function(e) {
    if (self.dragging) {
      self.setSelection(self.activeCoords[0], self.activeCoords[1], e.target.coords[0], e.target.coords[1]);
    }
  };

  self.mouseDown = function(e) {
    self.dragging = true;
  };

  self.mouseUp = function(e) {
    self.dragging = false;
  };

  if (table) self.setTable(table);
}
