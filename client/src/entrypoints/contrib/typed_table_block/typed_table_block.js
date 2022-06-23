/* global $ */

import { escapeHtml as h } from '../../../utils/text';

export class TypedTableBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;

    // list of column definition objects, each consisting of fields:
    // * blockDef: the block definition object
    // * position: the 0-indexed position of this column within the list of columns
    //    (will change as new columns are inserted / deleted)
    // * id: the unique ID number assigned to this column, used in field name prefixes
    //    (will remain unchanged when new columns are inserted / deleted)
    // * typeInput: the hidden input element containing the block type
    // * positionInput: the hidden input element containing the column position
    // * deletedInput: the hidden input element indicating whether this column is deleted
    // * headingInput: the text input element for the column header
    this.columns = [];

    // list of row definition objects, each consisting of fields:
    // * blocks: list of block instances making up this row
    // * position: the 0-indexed position of this row within the list of rows
    //    (will change as new rows are inserted / deleted)
    // * id: the unique ID number assigned to this row, used in field name prefixes
    //    (will remain unchanged when new rows are inserted / deleted)
    // * positionInput: the hidden input element containing the row position
    // * deletedInput: the hidden input element indicating whether this row is deleted
    this.rows = [];

    this.columnCountIncludingDeleted = 0;
    this.rowCountIncludingDeleted = 0;
    this.prefix = prefix;
    this.childBlockDefsByName = {};
    this.blockDef.childBlockDefs.forEach((childBlockDef) => {
      this.childBlockDefsByName[childBlockDef.name] = childBlockDef;
    });

    const strings = this.blockDef.meta.strings;
    const dom = $(`
      <div class="typed-table-block ${h(this.blockDef.meta.classname || '')}">
        <input type="hidden" name="${h(
          prefix,
        )}-column-count" data-column-count value="0">
        <input type="hidden" name="${h(
          prefix,
        )}-row-count" data-row-count value="0">
        <div data-deleted-fields></div>
        <div class="typed-table-block__wrapper">
          <table>
            <thead>
              <tr>
                <th></th>
                <th class="control-cell">
                  <button type="button" class="button button-small button-secondary append-column" data-append-column>
                    ${h(strings.ADD_COLUMN)}
                  </button>
                </th>
              </tr>
            </thead>
            <tbody>
            </tbody>
            <tfoot>
              <tr>
                <td class="control-cell">
                  <button
                    type="button"
                    class="button button-small button-secondary button--icon text-replace prepend-row"
                    data-add-row
                    aria-label="${h(strings.ADD_ROW)}"
                    title="${h(strings.ADD_ROW)}"
                  >
                    <svg class="icon icon-plus icon" aria-hidden="true">
                      <use href="#icon-plus"></use>
                    </svg>
                  </button></td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    `);
    $(placeholder).replaceWith(dom);
    this.thead = dom.find('table > thead').get(0);
    this.tbody = dom.find('table > tbody').get(0);

    // Hidden field holding the number of columns, including deleted ones.
    // The server-side code will use this to find out the range of column indexes to
    // iterate over.
    this.columnCountInput = dom.find('input[data-column-count]').get(0);
    // Hidden field holding the number of rows, including deleted ones
    this.rowCountInput = dom.find('input[data-row-count]').get(0);

    // Container for the hidden fields that indicate whether a column of a given index
    // has been deleted. A deleted column is removed from the DOM, but we need this field
    // to persist (so that we know it's been deleted...) - so we can't store it in the
    // table as we do for the other metadata fields (type and position).
    this.deletedFieldsContainer = dom.find('[data-deleted-fields]').get(0);

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
    this.addColumnMenu = $('<ul class="add-column-menu"></ul>');
    this.blockDef.childBlockDefs.forEach((childBlockDef) => {
      const columnTypeButton = $(
        '<button type="button" class="button button-small"></button>',
      ).text(childBlockDef.meta.label);
      columnTypeButton.on('click', () => {
        if (this.addColumnCallback) this.addColumnCallback(childBlockDef);
        this.hideAddColumnMenu();
      });
      const li = $('<li></li>').append(columnTypeButton);
      this.addColumnMenu.append(li);
    });
    this.addColumnMenuBaseElement = null; // the element the add-column menu is attached to

    this.appendColumnButton.on('click', () => {
      this.toggleAddColumnMenu(this.appendColumnButton, (chosenBlockDef) => {
        this.insertColumn(this.columns.length, chosenBlockDef, {
          addInitialRow: true,
        });
      });
    });

    this.addRowButton.on('click', () => {
      this.insertRow(this.rows.length);
    });

    this.setState(initialState);
    if (initialError) {
      this.setError(initialError);
    }
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
    this.columnCountIncludingDeleted = 0;
    this.columnCountInput.value = 0;
    this.rowCountIncludingDeleted = 0;
    this.rowCountInput.value = 0;

    // remove all hidden fields from deletedFieldsContainer
    this.deletedFieldsContainer.replaceChildren();

    const headerRow = this.thead.children[0];
    // delete all header cells except for the control columns
    headerRow.replaceChildren(
      headerRow.firstElementChild,
      headerRow.lastElementChild,
    );
    this.appendColumnButton
      .text(this.blockDef.meta.strings.ADD_COLUMN)
      .removeClass('button--icon text-replace white')
      .removeAttr('aria-label')
      .removeAttr('title');

    // delete all body rows
    this.tbody.replaceChildren();
    this.addRowButton.hide();
  }

  insertColumn(index, blockDef, opts) {
    const column = {
      blockDef,
      position: index,
      id: this.columnCountIncludingDeleted,
    };
    this.columnCountIncludingDeleted++;
    // increase positions of columns after this one
    for (let i = index; i < this.columns.length; i++) {
      this.columns[i].position++;
      this.columns[i].positionInput.value = this.columns[i].position;
    }
    this.columns.splice(index, 0, column);
    this.columnCountInput.value = this.columnCountIncludingDeleted;

    // add new cell to the header row
    const headerRow = this.thead.children[0];
    const headerCells = headerRow.children;
    const newHeaderCell = document.createElement('th');
    // insertBefore is correct even for the last column, because the header row
    // has an extra final cell to contain the 'append column' button.
    // The +1 accounts for the 'control' column on the left side, holding the 'insert row' buttons.
    headerRow.insertBefore(newHeaderCell, headerCells[index + 1]);
    column.typeInput = document.createElement('input');
    column.typeInput.type = 'hidden';
    column.typeInput.name = this.prefix + '-column-' + column.id + '-type';
    column.typeInput.value = blockDef.name;
    newHeaderCell.appendChild(column.typeInput);
    column.positionInput = document.createElement('input');
    column.positionInput.type = 'hidden';
    column.positionInput.name = this.prefix + '-column-' + column.id + '-order';
    column.positionInput.value = index;
    newHeaderCell.appendChild(column.positionInput);
    column.deletedInput = document.createElement('input');
    column.deletedInput.type = 'hidden';
    column.deletedInput.name =
      this.prefix + '-column-' + column.id + '-deleted';
    column.deletedInput.value = '';
    this.deletedFieldsContainer.appendChild(column.deletedInput);

    const prependColumnButton = $(`<button type="button"
      class="button button-secondary button-small button--icon text-replace prepend-column"
      aria-label="${h(this.blockDef.meta.strings.INSERT_COLUMN)}"
      title="${h(this.blockDef.meta.strings.INSERT_COLUMN)}">
        <svg class="icon icon-plus icon" aria-hidden="true"><use href="#icon-plus"></use></svg>
      </button>`);
    $(newHeaderCell).append(prependColumnButton);
    prependColumnButton.on('click', () => {
      this.toggleAddColumnMenu(prependColumnButton, (chosenBlockDef) => {
        this.insertColumn(column.position, chosenBlockDef, {
          addInitialRow: true,
        });
      });
    });

    column.headingInput = document.createElement('input');
    column.headingInput.name =
      this.prefix + '-column-' + column.id + '-heading';
    column.headingInput.className = 'column-heading';
    column.headingInput.placeholder = this.blockDef.meta.strings.COLUMN_HEADING;
    newHeaderCell.appendChild(column.headingInput);

    const deleteColumnButton = $(`<button type="button"
      class="button button-secondary button-small button--icon text-replace no delete-column"
      aria-label="${h(this.blockDef.meta.strings.DELETE_COLUMN)}"
      title="${h(this.blockDef.meta.strings.DELETE_COLUMN)}">
        <svg class="icon icon-bin icon" aria-hidden="true"><use href="#icon-bin"></use></svg>
      </button>`);
    $(newHeaderCell).append(deleteColumnButton);
    deleteColumnButton.on('click', () => {
      this.deleteColumn(column.position);
    });

    // add new cell to each body row
    const initialCellState =
      this.blockDef.childBlockDefaultStates[blockDef.name];
    Array.from(this.tbody.children).forEach((tr, rowIndex) => {
      const row = this.rows[rowIndex];
      const cells = tr.children;
      const newCellElement = document.createElement('td');
      // insertBefore is correct even for the last column, because each row
      // has an extra final cell to contain the 'delete row' button.
      // The +1 accounts for the 'control' column on the left side, holding the 'insert row' buttons.
      tr.insertBefore(newCellElement, cells[index + 1]);
      const newCellBlock = this.initCell(
        newCellElement,
        column,
        row,
        initialCellState,
      );
      row.blocks.splice(index, 0, newCellBlock);
    });
    /* after first column is added, enable adding rows */
    this.addRowButton.show();
    this.appendColumnButton
      .html(
        '<svg class="icon icon-plus icon" aria-hidden="true"><use href="#icon-plus"></use></svg>',
      )
      .addClass('button--icon text-replace white')
      .attr('aria-label', this.blockDef.meta.strings.ADD_COLUMN)
      .addClass('button--icon text-replace white')
      .attr('aria-label', this.blockDef.meta.strings.ADD_COLUMN)
      .attr('title', this.blockDef.meta.strings.ADD_COLUMN);

    if (opts && opts.addInitialRow && this.tbody.children.length === 0) {
      /* add an initial row */
      this.insertRow(0);
    }
    return column;
  }

  deleteColumn(index) {
    const column = this.columns[index];
    column.deletedInput.value = '1';
    const headerRow = this.thead.children[0];
    const headerCells = headerRow.children;
    headerRow.removeChild(headerCells[index + 1]);
    Array.from(this.tbody.children).forEach((tr, rowIndex) => {
      const cells = tr.children;
      tr.removeChild(cells[index + 1]);
      this.rows[rowIndex].blocks.splice(index, 1);
    });
    this.columns.splice(index, 1);

    // reduce position values of remaining columns after this one
    for (let i = index; i < this.columns.length; i++) {
      this.columns[i].position--;
      this.columns[i].positionInput.value = this.columns[i].position;
    }

    // if no columns remain, revert to initial empty state with no rows
    if (this.columns.length === 0) {
      this.clear();
    }
  }

  insertRow(index, initialStates) {
    const rowElement = document.createElement('tr');
    const row = {
      blocks: [],
      position: index,
      id: this.rowCountIncludingDeleted,
    };
    if (index < this.rows.length) {
      const followingRowElement = this.tbody.children[index];
      this.tbody.insertBefore(rowElement, followingRowElement);
    } else {
      this.tbody.appendChild(rowElement);
    }
    this.rows.splice(index, 0, row);
    this.rowCountIncludingDeleted++;
    this.rowCountInput.value = this.rowCountIncludingDeleted;

    // add a leading cell to contain the 'insert row' button
    const controlCellBefore = document.createElement('td');
    controlCellBefore.className = 'control-cell';
    rowElement.appendChild(controlCellBefore);
    const prependRowButton = $(`<button type="button"
      class="button button-secondary button-small button--icon text-replace prepend-row"
      aria-label="${h(this.blockDef.meta.strings.INSERT_ROW)}"
      title="${h(this.blockDef.meta.strings.INSERT_ROW)}">
        <svg class="icon icon-plus icon" aria-hidden="true"><use href="#icon-plus"></use></svg>
      </button>`);
    $(controlCellBefore).append(prependRowButton);
    prependRowButton.on('click', () => {
      this.insertRow(row.position);
    });

    this.columns.forEach((column, i) => {
      let initialState;
      if (initialStates) {
        initialState = initialStates[i];
      } else {
        // use block's default state
        initialState =
          this.blockDef.childBlockDefaultStates[column.blockDef.name];
      }
      const newCell = document.createElement('td');
      rowElement.appendChild(newCell);
      row.blocks[i] = this.initCell(newCell, column, row, initialState);
    });

    // add a trailing cell to contain the 'remove row' button
    const controlCellAfter = document.createElement('td');
    controlCellAfter.className = 'control-cell';
    rowElement.appendChild(controlCellAfter);

    row.positionInput = document.createElement('input');
    row.positionInput.type = 'hidden';
    row.positionInput.name = this.prefix + '-row-' + row.id + '-order';
    row.positionInput.value = row.position;
    controlCellAfter.appendChild(row.positionInput);

    const deleteRowButton = $(`<button type="button"
      class="button button-secondary button-small button--icon text-replace no delete-row"
      aria-label="${h(this.blockDef.meta.strings.DELETE_ROW)}"
      title="${h(this.blockDef.meta.strings.DELETE_ROW)}">
        <svg class="icon icon-bin icon" aria-hidden="true"><use href="#icon-bin"></use></svg>
      </button>`);
    $(controlCellAfter).append(deleteRowButton);
    deleteRowButton.on('click', () => {
      this.deleteRow(row.position);
    });

    row.deletedInput = document.createElement('input');
    row.deletedInput.type = 'hidden';
    row.deletedInput.name = this.prefix + '-row-' + row.id + '-deleted';
    row.deletedInput.value = '';
    this.deletedFieldsContainer.appendChild(row.deletedInput);

    // increment positions of subsequent rows
    for (let i = index + 1; i < this.rows.length; i++) {
      this.rows[i].position++;
      this.rows[i].positionInput.value = this.rows[i].position;
    }

    return row;
  }

  deleteRow(index) {
    const row = this.rows[index];
    row.deletedInput.value = '1';
    const rowElement = this.tbody.children[index];
    this.tbody.removeChild(rowElement);
    this.rows.splice(index, 1);

    // reduce position values of remaining rows after this one
    for (let i = index; i < this.rows.length; i++) {
      this.rows[i].position--;
      this.rows[i].positionInput.value = this.rows[i].position;
    }
  }

  initCell(cell, column, row, initialState) {
    const placeholder = document.createElement('div');
    cell.appendChild(placeholder);
    const cellPrefix = this.prefix + '-cell-' + row.id + '-' + column.id;
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
      state.rows.forEach((row, index) => {
        this.insertRow(index, row.values);
      });
    }
  }

  setError(errorList) {
    if (errorList.length !== 1) {
      return;
    }
    const error = errorList[0];
    if (error.cellErrors) {
      for (const [rowIndex, rowErrors] of Object.entries(error.cellErrors)) {
        for (const [colIndex, cellError] of Object.entries(rowErrors)) {
          this.rows[rowIndex].blocks[colIndex].setError([cellError]);
        }
      }
    }
  }

  getState() {
    const state = {
      columns: this.columns.map((column) => ({
        type: column.blockDef.name,
        heading: column.headingInput.value,
      })),
      rows: this.rows.map((row) => ({
        values: row.blocks.map((block) => block.getState()),
      })),
    };
    return state;
  }

  getValue() {
    const value = {
      columns: this.columns.map((column) => ({
        type: column.blockDef.name,
        heading: column.headingInput.value,
      })),
      rows: this.rows.map((row) => ({
        values: row.blocks.map((block) => block.getValue()),
      })),
    };
    return value;
  }

  getTextLabel(opts) {
    /* Use as many child text labels as we can fit into maxLength */
    const maxLength = opts && opts.maxLength;
    let result = '';

    for (const row of this.rows) {
      for (const block of row.blocks) {
        if (block.getTextLabel) {
          const childLabel = block.getTextLabel({ maxLength });
          if (childLabel) {
            if (!result) {
              // always use the first child, truncated as necessary
              result = childLabel;
            } else {
              const newResult = result + ', ' + childLabel;
              if (maxLength && newResult.length > maxLength - 1) {
                // too long, so don't add this; return the current list with an ellipsis instead
                if (!result.endsWith('…')) result += '…';
                return result;
              }
              result = newResult;
            }
          }
        }
      }
    }
    return result;
  }

  focus(opts) {
    if (!this.columns.length) {
      this.appendColumnButton.focus();
    } else if (!this.rows.length) {
      this.addRowButton.focus();
    } else {
      this.rows[0].blocks[0].focus(opts);
    }
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
    return new TypedTableBlock(
      this,
      placeholder,
      prefix,
      initialState,
      initialError,
    );
  }
}
window.telepath.register(
  'wagtail.contrib.typed_table_block.blocks.TypedTableBlock',
  TypedTableBlockDefinition,
);

export class TypedTableBlockValidationError {
  constructor(cellErrors) {
    this.cellErrors = cellErrors;
  }
}
window.telepath.register(
  'wagtail.contrib.typed_table_block.TypedTableBlockValidationError',
  TypedTableBlockValidationError,
);
