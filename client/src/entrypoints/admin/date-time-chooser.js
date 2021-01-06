import $ from 'jquery';
import { Widget } from './telepath/widgets';

/* global wagtailConfig */

$.fn.datetimepicker.defaults.i18n.wagtail_custom_locale = {
  months: wagtailConfig.STRINGS.MONTHS,
  dayOfWeek: wagtailConfig.STRINGS.WEEKDAYS,
  dayOfWeekShort: wagtailConfig.STRINGS.WEEKDAYS_SHORT,
};
$.datetimepicker.setLocale('wagtail_custom_locale');

// Compare two date objects. Ignore minutes and seconds.
function dateEqual(x, y) {
  return x.getDate() === y.getDate() &&
       x.getMonth() === y.getMonth() &&
       x.getYear() === y.getYear();
}
window.dateEqual = dateEqual;

/*
Remove the xdsoft_current css class from markup unless the selected date is currently in view.
Keep the normal behaviour if the home button is clicked.
 */
function hideCurrent(current, input) {
  const selected = new Date(input[0].value);
  if (!dateEqual(selected, current)) {
    $(this).find('.xdsoft_datepicker .xdsoft_current:not(.xdsoft_today)').removeClass('xdsoft_current');
  }
}
window.hideCurrent = hideCurrent;

class BaseDateTimeWidget extends Widget {
  constructor(options) {
      this.options = options;
  }

  render(placeholder, name, id) {
      const element = document.createElement('input');
      element.type = 'text';
      element.name = name;
      element.id = id;
      placeholder.replaceWith(element);

      this.initChooserFn(id, this.options);

      return {
          getValue() {
              return element.value;
          },
          getState() {
              return element.value;
          },
          setState(state) {
              element.value = state;
          }
      }
  }
}

function initDateChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker($.extend({
      closeOnDateSelect: true,
      timepicker: false,
      scrollInput: false,
      format: 'Y-m-d',
      onGenerate: hideCurrent,
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  } else {
    $('#' + id).datetimepicker($.extend({
      timepicker: false,
      scrollInput: false,
      format: 'Y-m-d',
      onGenerate: hideCurrent,
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  }
}
window.initDateChooser = initDateChooser;

class AdminDateInput extends BaseDateTimeWidget {
  initChooserFn = initDateChooser;
}
window.telepath.register('wagtail.widgets.AdminDateInput', AdminDateInput);

function initTimeChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker($.extend({
      closeOnDateSelect: true,
      datepicker: false,
      scrollInput: false,
      format: 'H:i',
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  } else {
    $('#' + id).datetimepicker($.extend({
      datepicker: false,
      format: 'H:i',
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  }
}
window.initTimeChooser = initTimeChooser;

class AdminTimeInput extends BaseDateTimeWidget {
  initChooserFn = initTimeChooser;
}
window.telepath.register('wagtail.widgets.AdminTimeInput', AdminTimeInput);

function initDateTimeChooser(id, opts) {
  if (window.dateTimePickerTranslations) {
    $('#' + id).datetimepicker($.extend({
      closeOnDateSelect: true,
      format: 'Y-m-d H:i',
      scrollInput: false,
      onGenerate: hideCurrent,
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  } else {
    $('#' + id).datetimepicker($.extend({
      format: 'Y-m-d H:i',
      onGenerate: hideCurrent,
      onChangeDateTime(_, $el) {
        $el.get(0).dispatchEvent(new Event('change'));
      }
    }, opts || {}));
  }
}
window.initDateTimeChooser = initDateTimeChooser;


class AdminDateTimeInput extends BaseDateTimeWidget {
  initChooserFn = initDateTimeChooser;
}
window.telepath.register('wagtail.widgets.AdminDateTimeInput', AdminDateTimeInput);
