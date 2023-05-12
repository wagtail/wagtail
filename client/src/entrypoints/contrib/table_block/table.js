/* eslint-disable func-names, dot-notation */

/* global Handsontable */

import $ from 'jquery';
import { hasOwn } from '../../../utils/hasOwn';

function initTable(id, tableOptions) {
  const containerId = id + '-handsontable-container';
  const tableHeaderCheckboxId = id + '-handsontable-header';
  const colHeaderCheckboxId = id + '-handsontable-col-header';
  const tableCaptionId = id + '-handsontable-col-caption';
  const hiddenStreamInput = $('#' + id);
  const tableHeaderCheckbox = $('#' + tableHeaderCheckboxId);
  const colHeaderCheckbox = $('#' + colHeaderCheckboxId);
  const tableCaption = $('#' + tableCaptionId);
  const finalOptions = {};
  let hot = null;
  let dataForForm = null;
  let isInitialized = false;

  const getWidth = function () {
    return $('.w-field--table_input').closest('.w-panel').width();
  };
  const getHeight = function () {
    const tableParent = $('#' + id).parent();
    let htCoreHeight = 0;
    tableParent.find('.htCore').each(function () {
      htCoreHeight += $(this).height();
    });
    return htCoreHeight + tableParent.find('[data-field]').first().height();
  };
  const resizeTargets = [`#${containerId}`, '.wtHider', '.wtHolder'];
  const resizeHeight = function (height) {
    const currTable = $('#' + id);
    $.each(resizeTargets, function () {
      currTable.closest('[data-field]').find(this).height(height);
    });
  };
  function resizeWidth(width) {
    $.each(resizeTargets, function () {
      $(this).width(width);
    });
    const $field = $('.w-field--table_input');
    $field.width(width);
  }

  try {
    dataForForm = JSON.parse(hiddenStreamInput.val());
  } catch (e) {
    // do nothing
  }

  if (dataForForm !== null) {
    if (hasOwn(dataForForm, 'first_row_is_table_header')) {
      tableHeaderCheckbox.prop(
        'checked',
        dataForForm.first_row_is_table_header,
      );
    }
    if (hasOwn(dataForForm, 'first_col_is_header')) {
      colHeaderCheckbox.prop('checked', dataForForm.first_col_is_header);
    }
    if (hasOwn(dataForForm, 'table_caption')) {
      tableCaption.prop('value', dataForForm.table_caption);
    }
  }

  if (!hasOwn(tableOptions, 'width') || !hasOwn(tableOptions, 'height')) {
    // Size to parent field width if width is not given in tableOptions
    $(window).on('resize', () => {
      hot.updateSettings({
        width: getWidth(),
        height: getHeight(),
      });
      resizeWidth('100%');
    });
  }

  const getCellsClassnames = function () {
    const meta = hot.getCellsMeta();
    const cellsClassnames = [];
    for (let i = 0; i < meta.length; i += 1) {
      if (hasOwn(meta[i], 'className')) {
        cellsClassnames.push({
          row: meta[i].row,
          col: meta[i].col,
          className: meta[i].className,
        });
      }
    }
    return cellsClassnames;
  };

  const persist = function () {
    hiddenStreamInput.val(
      JSON.stringify({
        data: hot.getData(),
        cell: getCellsClassnames(),
        first_row_is_table_header: tableHeaderCheckbox.prop('checked'),
        first_col_is_header: colHeaderCheckbox.prop('checked'),
        table_caption: tableCaption.val(),
      }),
    );
  };

  const cellEvent = function (change, source) {
    if (source === 'loadData') {
      return; // don't save this change
    }

    persist();
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const metaEvent = function (row, column, key, value) {
    if (isInitialized && key === 'className') {
      persist();
    }
  };

  const initEvent = function () {
    isInitialized = true;
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const structureEvent = function (index, amount) {
    resizeHeight(getHeight());
    persist();
  };

  tableHeaderCheckbox.on('change', () => {
    persist();
  });

  colHeaderCheckbox.on('change', () => {
    persist();
  });

  tableCaption.on('change', () => {
    persist();
  });

  const defaultOptions = {
    afterChange: cellEvent,
    afterCreateCol: structureEvent,
    afterCreateRow: structureEvent,
    afterRemoveCol: structureEvent,
    afterRemoveRow: structureEvent,
    afterSetCellMeta: metaEvent,
    afterInit: initEvent,
    // contextMenu set via init, from server defaults
  };

  if (dataForForm !== null) {
    // Overrides default value from tableOptions (if given) with value from database
    if (hasOwn(dataForForm, 'data')) {
      defaultOptions.data = dataForForm.data;
    }
    if (hasOwn(dataForForm, 'cell')) {
      defaultOptions.cell = dataForForm.cell;
    }
  }

  Object.keys(defaultOptions).forEach((key) => {
    finalOptions[key] = defaultOptions[key];
  });
  Object.keys(tableOptions).forEach((key) => {
    finalOptions[key] = tableOptions[key];
  });

  hot = new Handsontable(document.getElementById(containerId), finalOptions);
  window.addEventListener('load', () => {
    // Render the table. Calling render also removes 'null' literals from empty cells.
    hot.render();
    resizeHeight(getHeight());
    window.dispatchEvent(new Event('resize'));
  });
}
window.initTable = initTable;

class TableInput {
  constructor(options, strings) {
    this.options = options;
    this.strings = strings;
  }

  render(placeholder, name, id, initialState) {
    const container = document.createElement('div');
    container.innerHTML = `
      <div class="w-field__wrapper" data-field-wrapper>
        <label class="w-field__label" for="${id}-handsontable-header">${this.strings['Row header']}</label>
        <div class="w-field w-field--boolean_field w-field--checkbox_input" data-field>
          <div class="w-field__help" id="${id}-handsontable-header-helptext" data-field-help>
            <div class="help">${this.strings['Display the first row as a header.']}</div>
          </div>
          <div class="w-field__input" data-field-input>
            <input type="checkbox" id="${id}-handsontable-header" name="handsontable-header" aria-describedby="${id}-handsontable-header-helptext" />
          </div>
        </div>
      </div>
      <div class="w-field__wrapper" data-field-wrapper>
        <label class="w-field__label" for="${id}-handsontable-col-header">${this.strings['Column header']}</label>
        <div class="w-field w-field--boolean_field w-field--checkbox_input" data-field>
          <div class="w-field__help" id="${id}-handsontable-col-header-helptext" data-field-help>
            <div class="help">${this.strings['Display the first column as a header.']}</div>
          </div>
          <div class="w-field__input" data-field-input>
            <input type="checkbox" id="${id}-handsontable-col-header" name="handsontable-col-header" aria-describedby="${id}-handsontable-col-header-helptext" />
          </div>
        </div>
      </div>
      <div class="w-field__wrapper" data-field-wrapper>
        <label class="w-field__label" for="${id}-handsontable-col-caption">${this.strings['Table caption']}</label>
        <div class="w-field w-field--char_field w-field--text_input" data-field>
          <div class="w-field__help" id="${id}-handsontable-col-caption-helptext" data-field-help>
            <div class="help">${this.strings['A heading that identifies the overall topic of the table, and is useful for screen reader users']}</div>
          </div>
          <div class="w-field__input" data-field-input>
            <input type="text" id="${id}-handsontable-col-caption" name="handsontable-col-caption" aria-describedby="${id}-handsontable-col-caption-helptext" />
          </div>
        </div>
      </div>
      <div id="${id}-handsontable-container"></div>
      <input type="hidden" name="${name}" id="${id}" placeholder="${this.strings['Table']}">
    `;
    placeholder.replaceWith(container);

    const input = container.querySelector(`input[name="${name}"]`);
    const options = this.options;

    const widget = {
      getValue() {
        return JSON.parse(input.value);
      },
      getState() {
        return JSON.parse(input.value);
      },
      setState(state) {
        input.value = JSON.stringify(state);
        initTable(id, options);
      },
      // eslint-disable-next-line @typescript-eslint/no-empty-function
      focus() {},
    };
    widget.setState(initialState);
    return widget;
  }
}
window.telepath.register('wagtail.widgets.TableInput', TableInput);
