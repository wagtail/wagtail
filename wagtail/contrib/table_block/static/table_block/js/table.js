'use strict';

function initTable(id, tableOptions) {
    var containerId = id + '-handsontable-container';
    var tableHeaderCheckboxId = id + '-handsontable-header';
    var colHeaderCheckboxId = id + '-handsontable-col-header';
    var tableCaptionId = id + '-handsontable-col-caption';
    var hiddenStreamInput = $('#' + id);
    var tableHeaderCheckbox = $('#' + tableHeaderCheckboxId);
    var colHeaderCheckbox = $('#' + colHeaderCheckboxId);
    var tableCaption = $('#' + tableCaptionId);
    var hot;
    var defaultOptions;
    var finalOptions = {};
    var getCellsClassnames;
    var persist;
    var cellEvent;
    var metaEvent;
    var initEvent;
    var structureEvent;
    var dataForForm = null;
    var isInitialized = false;

    var getWidth = function() {
        return $('.widget-table_input').closest('.sequence-member-inner').width();
    };
    var getHeight = function() {
        var tableParent = $('#' + id).parent();
        return tableParent.find('.htCore').height() + (tableParent.find('.input').height() * 2);
    };
    var height = getHeight();
    var resizeTargets = ['.input > .handsontable', '.wtHider', '.wtHolder'];
    var resizeHeight = function(height) {
        var currTable = $('#' + id);
        $.each(resizeTargets, function() {
            currTable.closest('.field-content').find(this).height(height);
        });
    };
    function resizeWidth(width) {
        $.each(resizeTargets, function() {
            $(this).width(width);
        });
        var parentDiv = $('.widget-table_input').parent();
        parentDiv.find('.field-content').width(width);
        parentDiv.find('.fieldname-table .field-content .field-content').width('80%');
    }

    try {
        dataForForm = JSON.parse(hiddenStreamInput.val());
    } catch (e) {
        // do nothing
    }

    if (dataForForm !== null) {
        if (dataForForm.hasOwnProperty('first_row_is_table_header')) {
            tableHeaderCheckbox.prop('checked', dataForForm.first_row_is_table_header);
        }
        if (dataForForm.hasOwnProperty('first_col_is_header')) {
            colHeaderCheckbox.prop('checked', dataForForm.first_col_is_header);
        }
        if (dataForForm.hasOwnProperty('table_caption')) {
            tableCaption.prop('value', dataForForm.table_caption);
        }
    }

    if (!tableOptions.hasOwnProperty('width') || !tableOptions.hasOwnProperty('height')) {
        // Size to parent .sequence-member-inner width if width is not given in tableOptions
        $(window).on('resize', function() {
            hot.updateSettings({
                width: getWidth(),
                height: getHeight()
            });
            resizeWidth('100%');
        });
    }

    getCellsClassnames = function() {
        var meta = hot.getCellsMeta();
        var cellsClassnames = []
        for (var i = 0; i < meta.length; i++) {
            if (meta[i].hasOwnProperty('className')) {
                cellsClassnames.push({
                    row: meta[i].row,
                    col: meta[i].col,
                    className: meta[i].className
                });
            }
        }
        return cellsClassnames;
    };

    persist = function() {
        hiddenStreamInput.val(JSON.stringify({
            data: hot.getData(),
            cell: getCellsClassnames(),
            first_row_is_table_header: tableHeaderCheckbox.prop('checked'),
            first_col_is_header: colHeaderCheckbox.prop('checked'),
            table_caption: tableCaption.val()
        }));
    };

    cellEvent = function(change, source) {
        if (source === 'loadData') {
            return; //don't save this change
        }

        persist();
    };

    metaEvent = function(row, column, key, value) {
        if (isInitialized && key === 'className') {
            persist();
        }
    };

    initEvent = function() {
        isInitialized = true;
    };

    structureEvent = function(index, amount) {
        resizeHeight(getHeight());
        persist();
    };

    tableHeaderCheckbox.on('change', function() {
        persist();
    });

    colHeaderCheckbox.on('change', function() {
        persist();
    });

    tableCaption.on('change', function() {
        persist();
    });

    defaultOptions = {
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

    Object.keys(defaultOptions).forEach(function (key) {
        finalOptions[key] = defaultOptions[key];
    });
    Object.keys(tableOptions).forEach(function (key) {
        finalOptions[key] = tableOptions[key];
    });

    hot = new Handsontable(document.getElementById(containerId), finalOptions);
    hot.render(); // Call to render removes 'null' literals from empty cells

    // Apply resize after document is finished loading (parent .sequence-member-inner width is set)
    if ('resize' in $(window)) {
        resizeHeight(getHeight());
        $(window).on('load', function() {
            $(window).trigger('resize');
        });
    }
}
