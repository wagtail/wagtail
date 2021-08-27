/* global $ */

import { escapeHtml as h } from '../../../utils/text';


export class TypedTableBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    const state = initialState || {};
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.columns = [];
    this.columnIdIndex = 0;
    this.prefix = prefix;

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
        this.insertColumn(this.columns.length, chosenBlockDef);
      });
    });

    this.addRowButton.on('click', () => {
      this.addRow();
    });
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
  insertColumn(index, blockDef) {
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
    Array.from(this.thead.children).forEach(tr => {
      const cells = tr.children;
      const newCell = document.createElement('th');
      // insertBefore is correct even for the last column, because the header row
      // has an extra final cell to contain the 'append column' button
      tr.insertBefore(newCell, cells[index]);
    });
    // add new cell to each body row
    Array.from(this.tbody.children).forEach((tr, rowIndex) => {
      const cells = tr.children;
      const newCell = document.createElement('td');
      if (isLastColumn) {
        tr.appendChild(newCell);
      } else {
        tr.insertBefore(newCell, cells[index]);
      }
      this.initCell(newCell, column, rowIndex);
    });
    /* after first column is added, enable adding rows */
    this.addRowButton.show();
    this.appendColumnButton.text('+');
    /* if no rows exist, add an initial one */
    if (this.tbody.children.length === 0) {
      this.addRow();
    }
  }
  addRow() {
    const newRow = document.createElement('tr');
    const rowIndex = this.tbody.children.length;
    this.tbody.appendChild(newRow);
    this.rowCountInput.value = this.tbody.children.length;
    this.columns.forEach(column => {
      const newCell = document.createElement('td');
      newRow.appendChild(newCell);
      this.initCell(newCell, column, rowIndex);
    });
  }
  initCell(cell, column, rowIndex) {
    const placeholder = document.createElement('div');
    cell.appendChild(placeholder);
    const cellPrefix = this.prefix + '-cell-' + rowIndex + '-' + column.id;
    const defaultState = this.blockDef.childBlockDefaultStates[column.blockDef.name];
    column.blockDef.render(placeholder, cellPrefix, defaultState, null);
  }

  setState(state) {
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];
  }

  getState() {
  }

  getValue() {
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
