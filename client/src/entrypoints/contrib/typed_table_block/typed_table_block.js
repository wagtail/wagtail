/* global $ */

import { escapeHtml as h } from '../../../utils/text';


export class TypedTableBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    const state = initialState || {};
    this.blockDef = blockDef;
    this.type = blockDef.name;
    this.columns = [];

    const dom = $(`
      <div class="typed-table-block ${h(this.blockDef.meta.classname || '')}">
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
    };
    this.columns.splice(index, 0, column);
    Array.from(this.thead.children).forEach(tr => {
      const cells = tr.children;
      const newCell = document.createElement('th');
      tr.insertBefore(newCell, cells[index]);
    });
    Array.from(this.tbody.children).forEach(tr => {
      const cells = tr.children;
      const newCell = document.createElement('td');
      tr.insertBefore(newCell, cells[index]);
      this.initCell(newCell, blockDef);
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
    this.tbody.appendChild(newRow);
    this.columns.forEach(column => {
      const newCell = document.createElement('td');
      newRow.appendChild(newCell);
      this.initCell(newCell, column.blockDef);
    });
  }
  initCell(cell, blockDef) {
    const placeholder = document.createElement('div');
    cell.appendChild(placeholder);
    blockDef.render(placeholder, 'asdf', null, null);
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
  constructor(name, childBlockDefs, meta) {
    this.name = name;
    this.childBlockDefs = childBlockDefs;
    this.meta = meta;
  }

  render(placeholder, prefix, initialState, initialError) {
    return new TypedTableBlock(this, placeholder, prefix, initialState, initialError);
  }
}
window.telepath.register('wagtail.contrib.typed_table_block.blocks.TypedTableBlock', TypedTableBlockDefinition);
