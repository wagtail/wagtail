'use strict';

function initTable(id, tableOptions) {
    var containerId = id + '-handsontable-container';
    var tableHeaderId = id + '-handsontable-header';
    var colHeaderId = id + '-handsontable-col-header';
    var headerChoiceId = id + '-table-header-choice';
    var tableCaptionId = id + '-handsontable-col-caption';
    var hiddenStreamInput = $('#' + id);
    var tableHeader = $('#' + tableHeaderId);
    var colHeader = $('#' + colHeaderId);
    var headerChoice = $('#' + headerChoiceId);
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
        return tableParent.find('.htCore').height();
    };
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
    var setHiddenHeaderValues = function(headerChoice) {
        if (headerChoice == 'row') {
            tableHeader.prop('value', true);
            colHeader.prop('value', null);
        }
        if (headerChoice == 'column') {
            tableHeader.prop('value', null);
            colHeader.prop('value', true);
        }
        if (headerChoice == 'both') {
            tableHeader.prop('value', true);
            colHeader.prop('value', true);
        }
        if (headerChoice == 'neither') {
            tableHeader.prop('value', null);
            colHeader.prop('value', null);
        }
    }

    try {
        dataForForm = JSON.parse(hiddenStreamInput.val());
    } catch (e) {
        // do nothing
    }

    if (dataForForm !== null) {
        if (dataForForm.hasOwnProperty('table_header_choice')) {
            headerChoice.prop('value', dataForForm.table_header_choice);
            setHiddenHeaderValues(dataForForm.table_header_choice);
        }
        if (dataForForm.hasOwnProperty('table_caption')) {
            tableCaption.prop('value', dataForForm.table_caption);
        }
    } else {
        if (tableOptions.hasOwnProperty('table_header_choice')) {
            headerChoice.prop('value', tableOptions.table_header_choice);
            setHiddenHeaderValues(tableOptions.table_header_choice);
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
            first_row_is_table_header: tableHeader.val(),
            first_col_is_header: colHeader.val(),
            table_header_choice: headerChoice.val(),
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

    headerChoice.on('change', function() {
        setHiddenHeaderValues(headerChoice.val());
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
