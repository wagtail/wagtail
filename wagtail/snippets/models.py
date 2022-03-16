from django.contrib.admin.utils import quote
from django.core import checks
from django.db.models import ForeignKey
from django.urls import reverse

from wagtail.admin.admin_url_finder import register_admin_url_finder
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.models import get_object_usage

from .widgets import AdminSnippetChooser

SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


class SnippetAdminURLFinder:
    # subclasses should define a 'model' attribute
    def __init__(self, user=None):
        if user:
            from wagtail.snippets.permissions import get_permission_name

            self.user_can_edit = user.has_perm(
                get_permission_name("change", self.model)
            )
        else:
            # skip permission checks
            self.user_can_edit = True

    def get_edit_url(self, instance):
        if self.user_can_edit:
            return reverse(
                "wagtailsnippets:edit",
                args=(
                    self.model._meta.app_label,
                    self.model._meta.model_name,
                    quote(instance.pk),
                ),
            )


def register_snippet(model):
    if model not in SNIPPET_MODELS:
        model.get_usage = get_object_usage
        model.usage_url = get_snippet_usage_url
        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)

        url_finder_class = type(
            "_SnippetAdminURLFinder", (SnippetAdminURLFinder,), {"model": model}
        )
        register_admin_url_finder(model, url_finder_class)

        @checks.register("panels")
        def modeladmin_model_check(app_configs, **kwargs):
            errors = check_panels_in_model(model, "snippets")
            return errors

        # Set up admin model forms to use AdminSnippetChooser for any ForeignKey to this model
        register_form_field_override(
            ForeignKey, to=model, override={"widget": AdminSnippetChooser(model=model)}
        )

    return model


def get_snippet_usage_url(self):
    return reverse(
        "wagtailsnippets:usage",
        args=(self._meta.app_label, self._meta.model_name, quote(self.pk)),
    )
