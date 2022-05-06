import json
import warnings

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms import widgets
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.staticfiles import versioned_static
from wagtail.coreutils import resolve_model_string
from wagtail.models import Page
from wagtail.telepath import register
from wagtail.utils.deprecation import RemovedInWagtail50Warning
from wagtail.utils.widgets import WidgetWithScript
from wagtail.widget_adapters import WidgetAdapter


class AdminChooser(WidgetWithScript, widgets.Input):
    choose_one_text = _("Choose an item")
    choose_another_text = _("Choose another item")
    clear_choice_text = _("Clear choice")
    link_to_chosen_text = _("Edit this item")
    show_edit_link = True
    show_clear_link = True

    # when looping over form fields, this one should appear in visible_fields, not hidden_fields
    # despite the underlying input being type="hidden"
    input_type = "hidden"
    is_hidden = False

    def __init__(self, **kwargs):
        warnings.warn(
            "wagtail.admin.widgets.chooser.AdminChooser is deprecated. "
            "Custom chooser subclasses should inherit from wagtail.admin.widgets.chooser.BaseChooser instead",
            category=RemovedInWagtail50Warning,
        )

        # allow choose_one_text / choose_another_text to be overridden per-instance
        if "choose_one_text" in kwargs:
            self.choose_one_text = kwargs.pop("choose_one_text")
        if "choose_another_text" in kwargs:
            self.choose_another_text = kwargs.pop("choose_another_text")
        if "clear_choice_text" in kwargs:
            self.clear_choice_text = kwargs.pop("clear_choice_text")
        if "link_to_chosen_text" in kwargs:
            self.link_to_chosen_text = kwargs.pop("link_to_chosen_text")
        if "show_edit_link" in kwargs:
            self.show_edit_link = kwargs.pop("show_edit_link")
        if "show_clear_link" in kwargs:
            self.show_clear_link = kwargs.pop("show_clear_link")
        super().__init__(**kwargs)

    def get_instance(self, model_class, value):
        # helper method for cleanly turning 'value' into an instance object.
        # DEPRECATED - subclasses should override WidgetWithScript.get_value_data instead
        if value is None:
            return None

        try:
            return model_class.objects.get(pk=value)
        except model_class.DoesNotExist:
            return None

    def get_instance_and_id(self, model_class, value):
        # DEPRECATED - subclasses should override WidgetWithScript.get_value_data instead
        if value is None:
            return (None, None)
        elif isinstance(value, model_class):
            return (value, value.pk)
        else:
            try:
                return (model_class.objects.get(pk=value), value)
            except model_class.DoesNotExist:
                return (None, None)

    def value_from_datadict(self, data, files, name):
        # treat the empty string as None
        result = super().value_from_datadict(data, files, name)
        if result == "":
            return None
        else:
            return result


class BaseChooser(widgets.Input):
    choose_one_text = _("Choose an item")
    choose_another_text = _("Choose another item")
    clear_choice_text = _("Clear choice")
    link_to_chosen_text = _("Edit this item")
    show_edit_link = True
    show_clear_link = True

    # when looping over form fields, this one should appear in visible_fields, not hidden_fields
    # despite the underlying input being type="hidden"
    input_type = "hidden"
    is_hidden = False

    def __init__(self, **kwargs):
        # allow choose_one_text / choose_another_text to be overridden per-instance
        if "choose_one_text" in kwargs:
            self.choose_one_text = kwargs.pop("choose_one_text")
        if "choose_another_text" in kwargs:
            self.choose_another_text = kwargs.pop("choose_another_text")
        if "clear_choice_text" in kwargs:
            self.clear_choice_text = kwargs.pop("clear_choice_text")
        if "link_to_chosen_text" in kwargs:
            self.link_to_chosen_text = kwargs.pop("link_to_chosen_text")
        if "show_edit_link" in kwargs:
            self.show_edit_link = kwargs.pop("show_edit_link")
        if "show_clear_link" in kwargs:
            self.show_clear_link = kwargs.pop("show_clear_link")
        super().__init__(**kwargs)

    def value_from_datadict(self, data, files, name):
        # treat the empty string as None
        result = super().value_from_datadict(data, files, name)
        if result == "":
            return None
        else:
            return result

    def render_html(self, name, value, attrs):
        """Render the HTML (non-JS) portion of the field markup"""
        return super().render(name, value, attrs)

    def get_value_data(self, value):
        # Perform any necessary preprocessing on the value passed to render() before it is passed
        # on to render_html / render_js_init. This is a good place to perform database lookups
        # that are needed by both render_html and render_js_init. Return value is arbitrary
        # (we only care that render_html / render_js_init can accept it), but will typically be
        # a dict of data needed for rendering: id, title etc.
        return value

    def render(self, name, value, attrs=None, renderer=None):
        # no point trying to come up with sensible semantics for when 'id' is missing from attrs,
        # so let's make sure it fails early in the process
        try:
            id_ = attrs["id"]
        except (KeyError, TypeError):
            raise TypeError("BaseChooser cannot be rendered without an 'id' attribute")

        value_data = self.get_value_data(value)
        widget_html = self.render_html(name, value_data, attrs)

        js = self.render_js_init(id_, name, value_data)
        out = "{0}<script>{1}</script>".format(widget_html, js)
        return mark_safe(out)

    def render_js_init(self, id_, name, value):
        return ""


class AdminPageChooser(BaseChooser):
    choose_one_text = _("Choose a page")
    choose_another_text = _("Choose another page")
    link_to_chosen_text = _("Edit this page")

    def __init__(
        self, target_models=None, can_choose_root=False, user_perms=None, **kwargs
    ):
        super().__init__(**kwargs)

        if target_models:
            if not isinstance(target_models, (set, list, tuple)):
                # assume we've been passed a single instance; wrap it as a list
                target_models = [target_models]

            # normalise the list of target models to a list of page classes
            cleaned_target_models = []
            for model in target_models:
                try:
                    cleaned_target_models.append(resolve_model_string(model))
                except (ValueError, LookupError):
                    raise ImproperlyConfigured(
                        "Could not resolve %r into a model. "
                        "Model names should be in the form app_label.model_name"
                        % (model,)
                    )
        else:
            cleaned_target_models = [Page]

        if len(cleaned_target_models) == 1 and cleaned_target_models[0] is not Page:
            model_name = cleaned_target_models[0]._meta.verbose_name.title()
            self.choose_one_text += " (" + model_name + ")"

        self.user_perms = user_perms
        self.target_models = cleaned_target_models
        if len(self.target_models) == 1:
            self.model = self.target_models[0]
        else:
            self.model = Page
        self.can_choose_root = bool(can_choose_root)

    @property
    def model_names(self):
        return [
            "{app}.{model}".format(
                app=model._meta.app_label, model=model._meta.model_name
            )
            for model in self.target_models
        ]

    @property
    def client_options(self):
        # a JSON-serializable representation of the configuration options needed for the
        # client-side behaviour of this widget
        return {
            "model_names": self.model_names,
            "can_choose_root": self.can_choose_root,
            "user_perms": self.user_perms,
        }

    def get_value_data(self, value):
        if value is None:
            return None
        elif isinstance(value, Page):
            page = value.specific
        else:  # assume page ID
            try:
                page = self.model.objects.get(pk=value)
            except self.model.DoesNotExist:
                return None

            page = page.specific

        edit_url = AdminURLFinder().get_edit_url(page)
        parent_page = page.get_parent()
        return {
            "id": page.pk,
            "display_title": page.get_admin_display_title(),
            "parent_id": parent_page.pk if parent_page else None,
            "edit_url": edit_url,
        }

    def render_html(self, name, value_data, attrs):
        value_data = value_data or {}
        original_field_html = super().render_html(name, value_data.get("id"), attrs)

        return render_to_string(
            "wagtailadmin/widgets/chooser.html",
            {
                "widget": self,
                "original_field_html": original_field_html,
                "attrs": attrs,
                "value": bool(
                    value_data
                ),  # only used by chooser.html to identify blank values
                "display_title": value_data.get("display_title", ""),
                "edit_url": value_data.get("edit_url", ""),
                "icon": "doc-empty-inverse",
                "classname": "page-chooser",
                "chooser_url": reverse("wagtailadmin_choose_page"),
            },
        )

    def render_js_init(self, id_, name, value_data):
        value_data = value_data or {}
        return "createPageChooser({id}, {parent}, {options});".format(
            id=json.dumps(id_),
            parent=json.dumps(value_data.get("parent_id")),
            options=json.dumps(self.client_options),
        )

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/page-chooser-modal.js"),
                versioned_static("wagtailadmin/js/page-chooser.js"),
            ]
        )


class PageChooserAdapter(WidgetAdapter):
    js_constructor = "wagtail.widgets.PageChooser"

    def js_args(self, widget):
        return [
            widget.render_html("__NAME__", None, attrs={"id": "__ID__"}),
            widget.id_for_label("__ID__"),
            widget.client_options,
        ]


register(PageChooserAdapter(), AdminPageChooser)
