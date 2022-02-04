/* eslint-disable func-names, dot-notation */

/* global Handsontable */

import $ from 'jquery';

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
    return $('.widget-table_input').closest('.sequence-member-inner').width();
  };
  const getHeight = function () {
    const tableParent = $('#' + id).parent();
    return (
      tableParent.find('.htCore').height() +
      tableParent.find('.input').height() * 2
    );
  };
  const resizeTargets = ['.input > .handsontable', '.wtHider', '.wtHolder'];
  const resizeHeight = function (height) {
    const currTable = $('#' + id);
    $.each(resizeTargets, function () {
      currTable.closest('.field-content').find(this).height(height);
    });
  };
  function resizeWidth(width) {
    $.each(resizeTargets, function () {
      $(this).width(width);
    });
    const parentDiv = $('.widget-table_input').parent();
    parentDiv.find('.field-content').width(width);
    parentDiv
      .find('.fieldname-table .field-content .field-content')
      .width('80%');
  }

  try {
    dataForForm = JSON.parse(hiddenStreamInput.val());
  } catch (e) {
    // do nothing
  }

  if (dataForForm !== null) {
    if (dataForForm.hasOwnProperty('first_row_is_table_header')) {
      tableHeaderCheckbox.prop(
        'checked',
        dataForForm.first_row_is_table_header,
      );
    }
    if (dataForForm.hasOwnProperty('first_col_is_header')) {
      colHeaderCheckbox.prop('checked', dataForForm.first_col_is_header);
    }
    if (dataForForm.hasOwnProperty('table_caption')) {
      tableCaption.prop('value', dataForForm.table_caption);
    }
  }

  if (
    !tableOptions.hasOwnProperty('width') ||
    !tableOptions.hasOwnProperty('height')
  ) {
    // Size to parent .sequence-member-inner width if width is not given in tableOptions
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
    for (let i = 0; i < meta.length; i++) {
      if (meta[i].hasOwnProperty('className')) {
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
    if (dataForForm.hasOwnProperty('data')) {
      defaultOptions.data = dataForForm.data;
    }
    if (dataForForm.hasOwnProperty('cell')) {
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
  hot.render(); // Call to render removes 'null' literals from empty cells

  // Apply resize after document is finished loading (parent .sequence-member-inner width is set)
  if ('resize' in $(window)) {
    resizeHeight(getHeight());
    $(window).on('load', () => {
      $(window).trigger('resize');
    });
  }
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
      <div class="field boolean_field widget-checkbox_input">
        <label for="${id}-handsontable-header">${this.strings['Row header']}</label>
        <div class="field-content">
          <div class="input">
            <input type="checkbox" id="${id}-handsontable-header" name="handsontable-header" />
          </div>
          <p class="help">${this.strings['Display the first row as a header.']}</p>
        </div>
      </div>
      <br/>
      <div class="field boolean_field widget-checkbox_input">
        <label for="${id}-handsontable-col-header">${this.strings['Column header']}</label>
        <div class="field-content">
          <div class="input">
            <input type="checkbox" id="${id}-handsontable-col-header" name="handsontable-col-header" />
          </div>
          <p class="help">${this.strings['Display the first column as a header.']}</p>
        </div>
      </div>
      <br/>
      <div class="field">
          <label for="${id}-handsontable-col-caption">${this.strings['Table caption']}</label>
          <div class="field-content">
            <div class="input">
            <input type="text" id="${id}-handsontable-col-caption" name="handsontable-col-caption" />
          </div>
          <p class="help">
            ${this.strings['A heading that identifies the overall topic of the table, and is useful for screen reader users']}
          </p>
        </div>
      </div>
      <br/>
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
