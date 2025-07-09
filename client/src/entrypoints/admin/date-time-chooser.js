import $ from 'jquery';
import {
  dateEqual,
  hideCurrent,
  initDateChooser,
  initDateTimeChooser,
  initTimeChooser,
} from '../../includes/dateTimeChooser';

/* global wagtailConfig */

$.fn.datetimepicker.defaults.i18n.wagtail_custom_locale = {
  months: wagtailConfig.STRINGS.MONTHS,
  dayOfWeek: wagtailConfig.STRINGS.WEEKDAYS,
  dayOfWeekShort: wagtailConfig.STRINGS.WEEKDAYS_SHORT,
};
$.datetimepicker.setLocale('wagtail_custom_locale');

window.dateEqual = dateEqual;
window.hideCurrent = hideCurrent;
window.initDateChooser = initDateChooser;
window.initTimeChooser = initTimeChooser;
window.initDateTimeChooser = initDateTimeChooser;
