import json

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import BaseChooser
from wagtail.admin.widgets.button import ListingButton
from wagtail.telepath import register
from wagtail.widget_adapters import WidgetAdapter


class AdminSnippetChooser(BaseChooser):
    display_title_key = "string"
    icon = "snippet"
    classname = "snippet-chooser"

    def __init__(self, model, **kwargs):
        self.model = model
        name = self.model._meta.verbose_name
        self.choose_one_text = _("Choose %s") % name
        self.choose_another_text = _("Choose another %s") % name
        self.link_to_chosen_text = _("Edit this %s") % name

        super().__init__(**kwargs)

    def get_chooser_modal_url(self):
        try:
            return reverse(
                f"wagtailsnippetchoosers_{self.model._meta.app_label}_{self.model._meta.model_name}:choose"
            )
        except NoReverseMatch:
            # This most likely failed because the model is not registered as a snippet.
            # Check whether this is the case, and if so, output a more helpful error message
            from .models import get_snippet_models

            if self.model not in get_snippet_models():
                raise ImproperlyConfigured(
                    "AdminSnippetChooser cannot be used on non-snippet model %r"
                    % self.model
                )
            else:
                raise

    def render_js_init(self, id_, name, value_data):
        return "new SnippetChooser({id});".format(id=json.dumps(id_))

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailadmin/js/chooser-modal.js"),
                versioned_static("wagtailsnippets/js/snippet-chooser.js"),
            ]
        )


class SnippetChooserAdapter(WidgetAdapter):
    js_constructor = "wagtail.snippets.widgets.SnippetChooser"

    def js_args(self, widget):
        return [
            widget.render_html("__NAME__", None, attrs={"id": "__ID__"}),
            widget.id_for_label("__ID__"),
        ]

    @cached_property
    def media(self):
        return forms.Media(
            js=[
                versioned_static("wagtailsnippets/js/snippet-chooser-telepath.js"),
            ]
        )


register(SnippetChooserAdapter(), AdminSnippetChooser)


class SnippetListingButton(ListingButton):
    pass
