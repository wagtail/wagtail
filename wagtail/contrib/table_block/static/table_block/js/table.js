'use strict';

function initTable(id, tableOptions) {
    var containerId = id + '-handsontable-container';
    var tableHeaderCheckboxId = id + '-handsontable-header';
    var hiddenStreamInput = $('#' + id);
    var tableHeaderCheckbox = $('#' + tableHeaderCheckboxId);
    var hot;
    var finalOptions = {};
    var persist;
    var cellEvent;
    var structureEvent;
    var dataForForm = null;
    var getWidth = function() {
        return $('footer').innerWidth();
    };

    try {
        dataForForm = $.parseJSON(hiddenStreamInput.val());
    } catch (e) {
        // do nothing
    }

    for (var key in tableOptions) {
        if (tableOptions.hasOwnProperty(key)) {
            finalOptions[key] = tableOptions[key];
        }
    }

    if (dataForForm !== null) {
        if (dataForForm.hasOwnProperty('data')) {
            // Overrides default value from tableOptions (if given) with value from database
            finalOptions.data = dataForForm.data;
        }

        if (dataForForm.hasOwnProperty('first_row_is_table_header')) {
            tableHeaderCheckbox.prop('checked', dataForForm.first_row_is_table_header);
        }
    }

    if (!tableOptions.hasOwnProperty('width')) {
        // Size to footer width if width is not given in tableOptions
        $(window).resize(function() {
            hot.updateSettings({
                width: getWidth()
            });
        });
    }

    persist = function() {
        hiddenStreamInput.val(JSON.stringify({
            data: hot.getData(),
            first_row_is_table_header: tableHeaderCheckbox.prop('checked')
        }));
    };

    cellEvent = function(change, source) {
        if (source === 'loadData') {
            return; //don't save this change
        }

        persist();
    };

    structureEvent = function(index, amount) {
        persist();
    };

    tableHeaderCheckbox.change(function() {
        persist();
    });

    finalOptions.afterChange = cellEvent;
    finalOptions.afterCreateCol = structureEvent;
    finalOptions.afterCreateRow = structureEvent;
    finalOptions.afterRemoveCol = structureEvent;
    finalOptions.afterRemoveRow = structureEvent;
    hot = new Handsontable(document.getElementById(containerId), finalOptions);
    hot.render(); // Call to render removes 'null' literals from empty cells

    // Apply resize after document is finished loading (footer width is set)
    if ('resize' in $(window)) {
        $(window).load(function() {
            $(window).resize();
        });
    }
}
