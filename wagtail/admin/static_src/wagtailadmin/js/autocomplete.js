(function($) {
  window.wagtailAutocomplete = function ($input) {
    var lookupIndex = 0,
      lookupNextIndex = 0,
      newQuery = $input.val(),
      currentQuery = $input.data('currentQuery') || '',
      autocompleteUrl = $input.data('autocomplete-url'),
      $suggestionsContainer = $('.autocomplete-suggestions', $input.parent());

    $('li', $suggestionsContainer).on('click', function () {
      var $selection = $(this),
        $container = $selection.parent(),
        $target = $('#' + $container.data('target-id')),
        query = $selection.html();

      $target.val($selection.data('value'));
      $container.removeClass('autocomplete-suggestions--active').attr('aria-hidden', true);
      $input.data('currentQuery', query);
      $input.val(query);
    });

    // only do the query if it has changed for trimmed queries
    // eg. " " === "" and "firstword " === "firstword"
    if (currentQuery.trim() !== newQuery.trim()) {
      lookupNextIndex++;
      var index = lookupNextIndex;
      $.ajax({
        url: autocompleteUrl,
        data: { query: newQuery },
        success: function (data, status) {
          if (index > lookupIndex) {
            lookupIndex = index;
            $input.data('currentQuery', newQuery);
            var liHTML = '';
            $.each(data.items, function (i, item) {
              liHTML += '<li data-value="' + item.pk + '">' + item.label + '</li>';
            });
            $suggestionsContainer.addClass('autocomplete-suggestions--active').html(liHTML).attr('aria-hidden', false);
          }
        },
      });
    }
  };
})(jQuery);

function initializeAutocompleteWidget(id) {
  var $input = $('input[data-autocomplete-id=' + id + ']');
  $input.on('keyup cut paste change', function() {
    clearTimeout($input.data('timer'));
    $input.data('timer', setTimeout(window.wagtailAutocomplete($input), 200));
  });
}
