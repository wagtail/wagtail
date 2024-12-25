/* eslint-disable no-restricted-syntax */
/* global $ */

import { escapeHtml as h } from '../../../utils/text';
import { range } from '../../../utils/range';
import {
  addErrorMessages,
  removeErrorMessages,
} from '../../../includes/streamFieldErrors';

export class TypedTableBlock {
  constructor(blockDef, placeholder, prefix, initialState, initialError) {
    this.blockDef = blockDef;
    this.type = blockDef.name;

    this.caption = '';

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
    const captionID = `${h(prefix)}-caption`;
    const dom = $(`
      <div class="typed-table-block ${h(this.blockDef.meta.classname || '')}">
        <div class="w-field__wrapper" data-field-wrapper>
          <label class="w-field__label" for="${captionID}">
            ${strings.CAPTION}
          </label>
          <div class="w-field w-field--char_field w-field--text_input" data-field>
            <div class="w-field__help" data-field-help>
              <div class="help">
                ${strings.CAPTION_HELP_TEXT}
              </div>
            </div>
            <div class="w-field__input" data-field-input>
              <input type="text" id="${captionID}" name="${captionID}" value="" />
              <span></span>
            </div>
          </div>
        </div>
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
                <th aria-hidden="true"></th>
                <th class="control-cell">
                  <button type="button" class="button button-small button-secondary append-column" aria-expanded="false" data-append-column>
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
    this.container = dom;
    this.captionInput = dom.find(`#${captionID}`).get(0);
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
        <div class="c-sf-help">
          <div class="help">
            ${this.blockDef.meta.helpText}
          </div>
        </div>
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
        this.hideAddColumnMenu(this.addColumnMenuTrigger);
      });
      const li = $('<li></li>').append(columnTypeButton);
      this.addColumnMenu.append(li);
    });
    this.addColumnMenuTrigger = null; // the element the add-column menu is attached to

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

  showAddColumnMenu(triggeredElement, callback) {
    this.addColumnMenuTrigger?.attr('aria-expanded', 'false');
    this.addColumnMenuTrigger = triggeredElement;
    triggeredElement.after(this.addColumnMenu);
    triggeredElement.attr('aria-expanded', 'true');
    this.addColumnMenu.show();
    this.addColumnCallback = callback;
  }

  hideAddColumnMenu(triggeredElement) {
    triggeredElement.attr('aria-expanded', 'false');
    this.addColumnMenu.hide();
    this.addColumnMenuTrigger = null;
  }

  toggleAddColumnMenu(triggeredElement, callback) {
    if (this.addColumnMenuTrigger === triggeredElement) {
      this.hideAddColumnMenu(triggeredElement);
    } else {
      this.showAddColumnMenu(triggeredElement, callback);
    }
  }

  clear() {
    // reset to initial empty state with no rows or columns
    this.setCaption('');
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

  setCaption(caption) {
    this.caption = caption;
    this.captionInput.value = caption;
  }

  insertColumn(index, blockDef, opts) {
    const column = {
      blockDef,
      position: index,
      id: this.columnCountIncludingDeleted,
    };
    this.columnCountIncludingDeleted += 1;
    // increase positions of columns after this one
    range(index, this.columns.length).forEach((i) => {
      this.columns[i].position += 1;
      this.columns[i].positionInput.value = this.columns[i].position;
    });
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
      aria-expanded="false"
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
    column.headingInput.type = 'text';
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
      .attr('aria-expanded', 'false')
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
    range(index, this.columns.length).forEach((i) => {
      this.columns[i].position -= 1;
      this.columns[i].positionInput.value = this.columns[i].position;
    });

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
    this.rowCountIncludingDeleted += 1;
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
    range(index + 1, this.rows.length).forEach((i) => {
      this.rows[i].position += 1;
      this.rows[i].positionInput.value = this.rows[i].position;
    });

    return row;
  }

  deleteRow(index) {
    const row = this.rows[index];
    row.deletedInput.value = '1';
    const rowElement = this.tbody.children[index];
    this.tbody.removeChild(rowElement);
    this.rows.splice(index, 1);

    // reduce position values of remaining rows after this one
    range(index, this.rows.length).forEach((i) => {
      this.rows[i].position -= 1;
      this.rows[i].positionInput.value = this.rows[i].position;
    });
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
      this.setCaption(state.caption);
    }
  }

  setError(error) {
    if (!error) return;

    // Non block errors
    const container = this.container[0];
    removeErrorMessages(container);

    if (error.messages) {
      addErrorMessages(container, error.messages);
    }

    if (error.blockErrors) {
      for (const [rowIndex, rowErrors] of Object.entries(error.blockErrors)) {
        for (const [colIndex, cellError] of Object.entries(rowErrors)) {
          this.rows[rowIndex].blocks[colIndex].setError(cellError);
        }
      }
    }
  }

  getState() {
    const state = {
      columns: this.getColumnStates(),
      rows: this.rows.map((row) => ({
        values: row.blocks.map((block) => block.getState()),
      })),
      caption: this.caption,
    };
    return state;
  }

  getDuplicatedState() {
    return {
      columns: this.getColumnStates(),
      rows: this.rows.map((row) => ({
        values: row.blocks.map((block) =>
          block.getDuplicatedState === undefined
            ? block.getState()
            : block.getDuplicatedState(),
        ),
      })),
    };
  }

  getValue() {
    const value = {
      columns: this.getColumnStates(),
      rows: this.rows.map((row) => ({
        values: row.blocks.map((block) => block.getValue()),
      })),
      caption: this.caption,
    };
    return value;
  }

  getColumnStates() {
    return this.columns.map((column) => ({
      type: column.blockDef.name,
      heading: column.headingInput.value,
    }));
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
