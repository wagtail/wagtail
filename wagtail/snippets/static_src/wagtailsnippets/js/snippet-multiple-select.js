var updateRow = function(id, newValue) {
    var $row = $('table.listing tr#snippet-row-' + id);
    var $checklist = $row.find('input[type=checkbox].toggle-select-row');
    $checklist.prop('checked', newValue);
    if (newValue) {
        $row.addClass('selected');
    } else {
        $row.removeClass('selected');
    }
};

var updateDeleteButton = function(anySelected, newState) {
    var $deleteButton = $('a.button.delete-button');
    var ids = [];
    $.each(newState, function(id, newValue) {
        if (newValue) {
          ids.push(id);
        }
    });
    if (anySelected) {
        // hide button and add url
        $deleteButton.removeClass('u-hidden');
        var url = $deleteButton.data('url');
        url = url + $.param({ id: ids }, true);
        $deleteButton.attr('href', url);
    } else {
        // show button and remove url
        $deleteButton.addClass('u-hidden');
        $deleteButton.attr('href', null);
    }
};

var updateSelectAllCheckbox = function(value) {
    var $selectAllCheckbox = $('table.listing input[type=checkbox].toggle-select-all');
    $selectAllCheckbox.prop('checked', value);
};

var buildSelectedState = function() {
    // prepare the selected state -- {3: true, 4: false}
    var state = {};
    var $rows = $('table.listing tbody tr input[type=checkbox].toggle-select-row');
    $.each($rows, function (index, row) {
        var $row = $(row);
        var selected = $row.prop('checked');
        var id = $row.attr('value');
        state[id] = selected;
    });
    return state;
};

var updateSelectedState = function(state, newValue, idToUpdate) {
    if (idToUpdate === null) {
        // update all rows
        $.each(state, function (id, currentValue) {
            state[id] = newValue;
        });
    } else {
        // update single row
        state[idToUpdate] = newValue;
    }
    return state;
};

var updateView = function(newState) {
      var allSelected = true;
      var anySelected = false;
      var countOfUnselected = 0;
      var countOfSelected = 0;

      // update each row with the new value (selected or not)
      $.each(newState, function (id, newValue) {
          updateRow(id, newValue);
          if (newValue === false) {
              countOfUnselected += 1;
          } else {
              countOfSelected += 1;
          }
      });

      // update the main checkbox for select all (if all are true)
      if (countOfUnselected >= 1) { allSelected = false; }
      updateSelectAllCheckbox(allSelected);

      // update the delete button
      if (countOfSelected >= 1) { anySelected = true; }
      updateDeleteButton(anySelected, newState);
};

var onListingCheckboxClick = function() {
    $('table.listing input[type="checkbox"]').on('click', function(event) {
        var $target = $(event.target);
        var setToValue = $target.prop('checked');
        var currentState = buildSelectedState();
        var id = null;
        if ($target.hasClass('toggle-select-row')) {
            id = $target.attr('value');
        }
        var newState = updateSelectedState(currentState, setToValue, id);
        updateView(newState);
    });
};

$(document).ready(onListingCheckboxClick);
