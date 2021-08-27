/* global $ */

import { escapeHtml as h } from '../../../utils/text';


export class TypedTableBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.columns = [];  // list of column definition objects
    this.rows = [];  // list of lists of block instances
    this.columnIdIndex = 0;
    this.prefix = prefix;
    this.childBlockDefsByName = {};
    this.blockDef.childBlockDefs.forEach(childBlockDef => {
      this.childBlockDefsByName[childBlockDef.name] = childBlockDef;
    });

    const dom = $(`
      <div class="typed-table-block ${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(prefix)}-column-count" data-column-count value="0">
        <input type="hidden" name="${h(prefix)}-row-count" data-row-count value="0">
        <table>
          <thead>
            <tr><th><button type="button" data-append-column>Add columns</button></th></tr>
          </thead>
          <tbody>
          </tbody>
        </table>
        <button type="button" data-add-row>Add row</button>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    this.thead = dom.find('table > thead').get(0);
    this.tbody = dom.find('table > tbody').get(0);
    this.columnCountInput = dom.find('input[data-column-count]').get(0);
    this.rowCountInput = dom.find('input[data-row-count]').get(0);
    this.appendColumnButton = dom.find('button[data-append-column]');
    this.addRowButton = dom.find('button[data-add-row]');
    this.addRowButton.hide();

    if (this.blockDef.meta.helpText) {
      // help text is left unescaped as per Django conventions
      dom.append(`
        <span>
          <div class="help">
            ${this.blockDef.meta.helpIcon}
            ${this.blockDef.meta.helpText}
          </div>
        </span>
      `);
    }

    this.addColumnCallback = null;
    this.addColumnMenu = $('<ul></ul>');
    this.blockDef.childBlockDefs.forEach(childBlockDef => {
      const columnTypeButton = $('<button type="button"></button>').text(childBlockDef.meta.label);
      columnTypeButton.on('click', () => {
        if (this.addColumnCallback) this.addColumnCallback(childBlockDef);
        this.hideAddColumnMenu();
      });
      const li = $('<li></li>').append(columnTypeButton);
      this.addColumnMenu.append(li);
    });
    this.addColumnMenuBaseElement = null;  // the element the add-column menu is attached to

    this.appendColumnButton.on('click', () => {
      this.toggleAddColumnMenu(this.appendColumnButton, (chosenBlockDef) => {
        this.insertColumn(this.columns.length, chosenBlockDef, { addInitialRow: true });
      });
    });

    this.addRowButton.on('click', () => {
      this.addRow();
    });

    this.setState(initialState);
  }

  showAddColumnMenu(baseElement, callback) {
    this.addColumnMenuBaseElement = baseElement;
    baseElement.after(this.addColumnMenu);
    this.addColumnMenu.show();
    this.addColumnCallback = callback;
  }
  hideAddColumnMenu() {
    this.addColumnMenu.hide();
    this.addColumnMenuBaseElement = null;
  }
  toggleAddColumnMenu(baseElement, callback) {
    if (this.addColumnMenuBaseElement === baseElement) {
      this.hideAddColumnMenu();
    } else {
      this.showAddColumnMenu(baseElement, callback);
    }
  }
  clear() {
    // reset to initial empty state with no rows or columns
    this.columns = [];
    this.rows = [];
    this.columnIdIndex = 0;
    this.columnCountInput.value = 0;
    this.rowCountInput.value = 0;
    const headerRow = this.thead.children[0];
    // delete all header cells except for the final one containing the 'append column' button
    headerRow.replaceChildren(headerRow.lastElementChild);
    this.appendColumnButton.text('Add columns');
    // delete all body rows
    this.tbody.replaceChildren();
    this.addRowButton.hide();
  }
  insertColumn(index, blockDef, opts) {
    const column = {
      blockDef,
      position: index,
      id: this.columnIdIndex,
    };
    this.columnIdIndex++;
    const isLastColumn = (index === this.columns.length);
    // increase positions of columns after this one
    for (let i = index; i < this.columns.length; i++) {
      this.columns[i].position++;
    }
    this.columns.splice(index, 0, column);
    this.columnCountInput.value = this.columns.length;

    // add new cell to the header row
    const headerRow = this.thead.children[0];
    const headerCells = headerRow.children;
    const newHeaderCell = document.createElement('th');
    // insertBefore is correct even for the last column, because the header row
    // has an extra final cell to contain the 'append column' button
    headerRow.insertBefore(newHeaderCell, headerCells[index]);
    column.headingInput = document.createElement('input');
    column.headingInput.name = this.prefix + '-heading-' + column.id;
    newHeaderCell.appendChild(column.headingInput);

    // add new cell to each body row
    const initialCellState = this.blockDef.childBlockDefaultStates[blockDef.name];
    Array.from(this.tbody.children).forEach((tr, rowIndex) => {
      const cells = tr.children;
      const newCellElement = document.createElement('td');
      if (isLastColumn) {
        tr.appendChild(newCellElement);
      } else {
        tr.insertBefore(newCellElement, cells[index]);
      }
      const newCellBlock = this.initCell(newCellElement, column, rowIndex, initialCellState);
      this.rows[rowIndex].splice(index, 0, newCellBlock);
    });
    /* after first column is added, enable adding rows */
    this.addRowButton.show();
    this.appendColumnButton.text('+');

    if (opts && opts.addInitialRow && this.tbody.children.length === 0) {
      /* add an initial row */
      this.addRow();
    }
    return column;
  }
  addRow(initialStates) {
    const newRowElement = document.createElement('tr');
    const newRow = [];
    const rowIndex = this.rows.length;
    this.tbody.appendChild(newRowElement);
    this.rows.push(newRow);
    this.rowCountInput.value = this.rows.length;
    this.columns.forEach((column, i) => {
      let initialState;
      if (initialStates) {
        initialState = initialStates[i];
      } else {
        // use block's default state
        initialState = this.blockDef.childBlockDefaultStates[column.blockDef.name];
      }
      const newCell = document.createElement('td');
      newRowElement.appendChild(newCell);
      newRow[i] = this.initCell(newCell, column, rowIndex, initialState);
    });
    return newRow;
  }
  initCell(cell, column, rowIndex, initialState) {
    const placeholder = document.createElement('div');
    cell.appendChild(placeholder);
    const cellPrefix = this.prefix + '-cell-' + rowIndex + '-' + column.id;
    return column.blockDef.render(placeholder, cellPrefix, initialState, null);
  }

  setState(state) {
    this.clear();
    if (state) {
      state.columns.forEach((columnData, index) => {
        const blockDef = this.childBlockDefsByName[columnData.type];
        const column = this.insertColumn(index, blockDef);
        column.headingInput.value = columnData.heading;
      });
      state.rows.forEach(row => {
        this.addRow(row.values);
      });
    }
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];
  }

  getState() {
    const state = {
      columns: this.columns.map(column => (
        { type: column.blockDef.name, heading: column.headingInput.value }
      )),
      rows: this.rows.map(row => (
        { values: row.map(block => block.getState()) }
      )),
    };
    return state;
  }

  getValue() {
    const value = {
      columns: this.columns.map(column => (
        { type: column.blockDef.name, heading: column.headingInput.value }
      )),
      rows: this.rows.map(row => (
        { values: row.map(block => block.getValue()) }
      )),
    };
    return value;
  }

  getTextLabel(opts) {
    // no usable label found
    return null;
  }

  focus(opts) {
  }
}

export class TypedTableBlockDefinition {
  constructor(name, childBlockDefs, childBlockDefaultStates, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.childBlockDefaultStates = childBlockDefaultStates;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new TypedTableBlock(this, placeholder, prefix, initialState, initialError);
  }
}
window.telepath.register('wagtail.contrib.typed_table_block.blocks.TypedTableBlock', TypedTableBlockDefinition);
