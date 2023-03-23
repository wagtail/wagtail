import json

from django.conf import settings
from django.forms import widgets
from django.utils.formats import get_format

from wagtail.admin.datetimepicker import to_datetimepicker_format

DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M"
DEFAULT_TIME_FORMAT = "%H:%M"


class AdminDateInput(widgets.DateInput):
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            "autocomplete": "off",
            "data-controller": "w-date",
            "data-w-date-mode-value": "date",
        }
        fmt = format
        if attrs:
            default_attrs.update(attrs)
        if fmt is None:
            fmt = getattr(settings, "WAGTAIL_DATE_FORMAT", DEFAULT_DATE_FORMAT)
        self.js_format = to_datetimepicker_format(fmt)
        super().__init__(attrs=default_attrs, format=fmt)

    def get_config(self):
        return {
            "dayOfWeekStart": get_format("FIRST_DAY_OF_WEEK"),
            "format": self.js_format,
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["attrs"]["data-w-date-options-value"] = json.dumps(
            self.get_config()
        )

        return context


class AdminTimeInput(widgets.TimeInput):
    def __init__(self, attrs=None, format=None):
        default_attrs = {
            "autocomplete": "off",
            "data-controller": "w-date",
            "data-w-date-mode-value": "time",
        }
        if attrs:
            default_attrs.update(attrs)
        fmt = format
        if fmt is None:
            fmt = getattr(settings, "WAGTAIL_TIME_FORMAT", DEFAULT_TIME_FORMAT)
        self.js_format = to_datetimepicker_format(fmt)
        super().__init__(attrs=default_attrs, format=fmt)

    def get_config(self):
        return {
            "format": self.js_format,
            "formatTime": self.js_format,
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["attrs"]["data-w-date-options-value"] = json.dumps(
            self.get_config()
        )

        return context


class AdminDateTimeInput(widgets.DateTimeInput):
    def __init__(
        self,
        attrs=None,
        format=None,
        time_format=None,
        js_overlay_parent_selector="body",
    ):
        default_attrs = {
            "autocomplete": "off",
            "data-controller": "w-date",
            "data-w-date-mode-value": "datetime",
        }
        fmt = format
        if attrs:
            default_attrs.update(attrs)
        if fmt is None:
            fmt = getattr(settings, "WAGTAIL_DATETIME_FORMAT", DEFAULT_DATETIME_FORMAT)
        time_fmt = time_format
        if time_fmt is None:
            time_fmt = getattr(settings, "WAGTAIL_TIME_FORMAT", DEFAULT_TIME_FORMAT)
        self.js_format = to_datetimepicker_format(fmt)
        self.js_time_format = to_datetimepicker_format(time_fmt)
        self.js_overlay_parent_selector = js_overlay_parent_selector
        super().__init__(attrs=default_attrs, format=fmt)

    def get_config(self):
        return {
            "dayOfWeekStart": get_format("FIRST_DAY_OF_WEEK"),
            "format": self.js_format,
            "formatTime": self.js_time_format,
            # The parentID option actually takes a CSS selector instead of an ID
            "parentID": self.js_overlay_parent_selector,
        }

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["attrs"]["data-w-date-options-value"] = json.dumps(
            self.get_config()
        )

        return context
