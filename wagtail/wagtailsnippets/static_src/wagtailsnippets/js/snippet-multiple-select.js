function updateDeleteButton() {
    var $chekedCheckboxes = $('table.listing tbody input[type="checkbox"]:checked');
    var $deleteButton = $('a.button.delete-button');
    var ids = [];
    $.map($chekedCheckboxes, function(checkbox) {
        ids.push(checkbox.id);
    })
    if ( ids.length === 0 ) {
        $deleteButton.addClass('disabled');
        $deleteButton.attr('href', null);
    } else {
        $deleteButton.removeClass('disabled');
        var url = $deleteButton.data('url');
        url = url + $.param({id: ids}, true);
        $deleteButton.attr('href', url);
    }
};

function updateAllRows(value, $rows, $checkboxes) {
    if (value === true) {
        $rows.addClass('selected');
        $checkboxes.prop('checked', true);
    } else {
        $rows.removeClass('selected');
        $checkboxes.prop('checked', false);
    }
};

function onCheckboxClick() {
    $('table.listing input[type="checkbox"]').on('click', function(event) {
        $target = $(event.target);
        value = $target.prop('checked');
        if ( $target.hasClass('toggle-select-row') ) {
            $row = $($target.closest('tr')[0]);
            $selectAllCheckbox = $('table.listing input[type="checkbox"].toggle-select-all');
            if (value === true) {
                $row.addClass('selected');
                unchekedCheckboxes = $('table.listing tbody input[type="checkbox"]:not(:checked)').length;
                if (unchekedCheckboxes === 0) {
                    $selectAllCheckbox.prop('checked', false);
                }
            } else {
                $row.removeClass('selected');
                $selectAllCheckbox.prop('checked', false);
            }
        } else if ( $target.hasClass('toggle-select-all') ) {
            $rows = $('table.listing tr');
            $checkboxes = $('table.listing input[type="checkbox"]');
            updateAllRows(value, $rows, $checkboxes);
        }
        updateDeleteButton();
    });
};

$( document ).ready(onCheckboxClick);
