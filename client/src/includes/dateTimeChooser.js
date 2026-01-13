/**
 * Helper functions for initializing date and time chooser inputs using jQuery datetimepicker.
 * These are made available in the `window` scope by entrypoints/admin/date-time-chooser.js,
 * and depend on jQuery and jquery.datetimepicker.js having been loaded.
 */

import $ from 'jquery';

/**
 * Compare two date objects. Ignore minutes and seconds.
 */
export function dateEqual(x, y) {
  return (
    x.getDate() === y.getDate() &&
    x.getMonth() === y.getMonth() &&
    x.getYear() === y.getYear()
  );
}

/**
 * Remove the xdsoft_current css class from markup unless the selected date is currently in view.
 * Keep the normal behavior if the home button is clicked.
 */
export function hideCurrent(current, input) {
  const selected = new Date(input[0].value);
  if (!dateEqual(selected, current)) {
    $(this)
      .find('.xdsoft_datepicker .xdsoft_current:not(.xdsoft_today)')
      .removeClass('xdsoft_current');
  }
}

/**
 * Initializes the date chooser.
 * @param {string} id
 * @param {object} opts
 */
export function initDateChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker(
      $.extend(
        {
          closeOnDateSelect: true,
          timepicker: false,
          scrollInput: false,
          format: 'Y-m-d',
          onGenerate: hideCurrent,
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  } else {
    $('#' + id).datetimepicker(
      $.extend(
        {
          timepicker: false,
          scrollInput: false,
          format: 'Y-m-d',
          onGenerate: hideCurrent,
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  }
}

/**
 * Initializes the time chooser.
 * @param {string} id
 * @param {object} opts
 */
export function initTimeChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker(
      $.extend(
        {
          closeOnDateSelect: true,
          datepicker: false,
          scrollInput: false,
          format: 'H:i',
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  } else {
    $('#' + id).datetimepicker(
      $.extend(
        {
          datepicker: false,
          format: 'H:i',
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  }
}

/**
 * Initializes the date and time chooser.
 * @param {string} id
 * @param {object} opts
 */
export function initDateTimeChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker(
      $.extend(
        {
          closeOnDateSelect: true,
          format: 'Y-m-d H:i',
          scrollInput: false,
          onGenerate: hideCurrent,
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  } else {
    $('#' + id).datetimepicker(
      $.extend(
        {
          format: 'Y-m-d H:i',
          onGenerate: hideCurrent,
          onChangeDateTime(_, $el) {
            $el.get(0).dispatchEvent(new Event('change', { bubbles: true }));
          },
        },
        opts || {},
      ),
    );
  }
}
