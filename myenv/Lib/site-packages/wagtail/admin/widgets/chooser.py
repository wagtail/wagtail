import json

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms import widgets
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from wagtail.admin.admin_url_finder import AdminURLFinder
from wagtail.admin.staticfiles import versioned_static
from wagtail.coreutils import resolve_model_string
from wagtail.models import Page
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter


class BaseChooser(widgets.Input):
    choose_one_text = _("Choose an item")
    choose_another_text = _("Choose another item")
    clear_choice_text = _("Clear choice")
    link_to_chosen_text = _("Edit this item")
    show_edit_link = True
    show_clear_link = True
    template_name = "wagtailadmin/widgets/chooser.html"
    display_title_key = (
        "title"  # key to use for the display title within the value data dict
    )
    icon = None
    classname = None
    model = None
    js_constructor = "Chooser"
    linked_fields = {}

    # when looping over form fields, this one should appear in visible_fields, not hidden_fields
    # despite the underlying input being type="hidden"
    input_type = "hidden"
    is_hidden = False

    def __init__(self, **kwargs):
        # allow attributes to be overridden by kwargs
        for var in [
            "choose_one_text",
            "choose_another_text",
            "clear_choice_text",
            "link_to_chosen_text",
            "show_edit_link",
            "show_clear_link",
            "icon",
            "linked_fields",
        ]:
            if var in kwargs:
                setattr(self, var, kwargs.pop(var))
        super().__init__(**kwargs)

    @cached_property
    def model_class(self):
        return resolve_model_string(self.model)

    def value_from_datadict(self, data, files, name):
        # treat the empty string as None
        result = super().value_from_datadict(data, files, name)
        if result == "":
            return None
        else:
            return result

    def get_hidden_input_context(self, name, value, attrs):
        """
        Return the context variables required to render the underlying hidden input element
        """
        return super().get_context(name, value, attrs)

    def render_hidden_input(self, name, value, attrs):
        """Render the HTML for the underlying hidden input element"""
        return self._render(
            "django/forms/widgets/input.html",
            self.get_hidden_input_context(name, value, attrs),
        )

    def get_chooser_modal_url(self):
        return reverse(self.chooser_modal_url_name)

    def get_context(self, name, value_data, attrs):
        original_field_html = self.render_hidden_input(
            name, value_data.get("id"), attrs
        )
        return {
            "widget": self,
            "original_field_html": original_field_html,
            "attrs": attrs,
            "value": bool(
                value_data
            ),  # only used by chooser.html to identify blank values
            "edit_url": value_data.get("edit_url", ""),
            "display_title": value_data.get(self.display_title_key, ""),
            "chooser_url": self.get_chooser_modal_url(),
            "icon": self.icon,
            "classname": self.classname,
        }

    def render_html(self, name, value_data, attrs):
        return render_to_string(
            self.template_name,
            self.get_context(name, value_data or {}, attrs),
        )

    def get_instance(self, value):
        """
        Given a value passed to this widget for rendering (which may be None, an id, or a model
        instance), return a model instance or None
        """
        if value is None:
            return None
        elif isinstance(value, self.model_class):
            return value
        else:  # assume instance ID
            try:
                return self.model_class.objects.get(pk=value)
            except self.model_class.DoesNotExist:
                return None

    def get_display_title(self, instance):
        """
        Return the text to display as the title for this instance
        """
        return str(instance)

    def get_value_data_from_instance(self, instance):
        """
        Given a model instance, return a value that we can pass to both the server-side template
        and the client-side rendering code (via telepath) that contains all the information needed
        for display. Typically this is a dict of id, title etc; it must be JSON-serialisable.
        """
        return {
            "id": instance.pk,
            "edit_url": AdminURLFinder().get_edit_url(instance),
            self.display_title_key: self.get_display_title(instance),
        }

    def get_value_data(self, value):
        """
        Given a value passed to this widget for rendering (which may be None, an id, or a model
        instance), return a value that we can pass to both the server-side template and the
        client-side rendering code (via telepath) that contains all the information needed
        for display. Typically this is a dict of id, title etc; it must be JSON-serialisable.
        """
        instance = self.get_instance(value)
        if instance:
            return self.get_value_data_from_instance(instance)

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
        out = f"{widget_html}<script>{js}</script>"
        return mark_safe(out)

    @property
    def base_js_init_options(self):
        """The set of options to pass to the JS initialiser that are constant every time this widget
        instance is rendered (i.e. do not vary based on id / name / value)"""
        opts = {
            "modalUrl": self.get_chooser_modal_url(),
        }
        if self.linked_fields:
            opts["linkedFields"] = self.linked_fields
        return opts

    def get_js_init_options(self, id_, name, value_data):
        return {**self.base_js_init_options}

    def render_js_init(self, id_, name, value_data):
        opts = self.get_js_init_options(id_, name, value_data)
        return f"new {self.js_constructor}({json.dumps(id_)}, {json.dumps(opts)});"

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/chooser-widget.js"),
            ]
        )


class BaseChooserAdapter(WidgetAdapter):
    js_constructor = "wagtail.admin.widgets.Chooser"

    def js_args(self, widget):
        return [
            widget.render_html("__NAME__", None, attrs={"id": "__ID__"}),
            widget.id_for_label("__ID__"),
            widget.base_js_init_options,
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/chooser-widget-telepath.js"),
            ]
        )


register(BaseChooserAdapter(), BaseChooser)


class AdminPageChooser(BaseChooser):
    choose_one_text = _("Choose a page")
    choose_another_text = _("Choose another page")
    link_to_chosen_text = _("Edit this page")
    display_title_key = "display_title"
    chooser_modal_url_name = "wagtailadmin_choose_page"
    icon = "doc-empty-inverse"
    classname = "page-chooser"
    js_constructor = "PageChooser"

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
    def base_js_init_options(self):
        # a JSON-serializable representation of the configuration options needed for the
        # client-side behaviour of this widget
        return {
            "modelNames": self.model_names,
            "canChooseRoot": self.can_choose_root,
            "userPerms": self.user_perms,
            **super().base_js_init_options,
        }

    def get_instance(self, value):
        instance = super().get_instance(value)
        if instance:
            return instance.specific

    def get_display_title(self, instance):
        return instance.get_admin_display_title()

    def get_value_data_from_instance(self, instance):
        data = super().get_value_data_from_instance(instance)
        parent_page = instance.get_parent()
        data["parent_id"] = parent_page.pk if parent_page else None
        return data

    def get_js_init_options(self, id_, name, value_data):
        opts = super().get_js_init_options(id_, name, value_data)
        value_data = value_data or {}
        parent_id = value_data.get("parent_id")
        if parent_id is not None:
            opts["parentId"] = parent_id
        return opts

    @property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/page-chooser-modal.js"),
                versioned_static("wagtailadmin/js/page-chooser.js"),
            ]
        )


class PageChooserAdapter(BaseChooserAdapter):
    js_constructor = "wagtail.widgets.PageChooser"

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/page-chooser-modal.js"),
                versioned_static("wagtailadmin/js/page-chooser-telepath.js"),
            ]
        )


class AdminPageMoveChooser(AdminPageChooser):
    def __init__(
        self, target_models=None, can_choose_root=False, user_perms=None, **kwargs
    ):
        self.pages_to_move = kwargs.pop("pages_to_move", [])
        super().__init__(
            target_models=target_models,
            can_choose_root=can_choose_root,
            user_perms=user_perms,
            **kwargs,
        )

    @property
    def base_js_init_options(self):
        return {
            "targetPages": self.pages_to_move,
            "matchSubclass": False,
            **super().base_js_init_options,
        }


register(PageChooserAdapter(), AdminPageChooser)
