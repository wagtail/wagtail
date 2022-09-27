from django.contrib.admin.utils import quote
from django.core import checks
from django.db.models import ForeignKey
from django.urls import reverse
from django.utils.module_loading import import_string

from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.viewsets import viewsets
from wagtail.models import ReferenceIndex

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
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        if self.user_can_edit:
            return reverse(
                f"wagtailsnippets_{app_label}_{model_name}:edit",
                args=[quote(instance.pk)],
            )


def register_snippet(model, viewset=None):
    if model not in SNIPPET_MODELS:
        from wagtail.snippets.views.chooser import SnippetChooserViewSet
        from wagtail.snippets.views.snippets import SnippetViewSet

        model.get_usage = lambda obj: ReferenceIndex.get_references_to(
            obj
        ).group_by_source_object()
        model.usage_url = get_snippet_usage_url
        model.get_admin_base_path = get_admin_base_path
        model.get_admin_url_namespace = get_admin_url_namespace

        if viewset is None:
            viewset = SnippetViewSet
        elif isinstance(viewset, str):
            viewset = import_string(viewset)

        admin_viewset = viewset(
            model.get_admin_url_namespace(),
            model=model,
            url_prefix=model.get_admin_base_path(),
        )

        chooser_viewset = SnippetChooserViewSet(
            f"wagtailsnippetchoosers_{model._meta.app_label}_{model._meta.model_name}",
            model=model,
            url_prefix=f"snippets/choose/{model._meta.app_label}/{model._meta.model_name}",
        )

        viewsets.register(admin_viewset)
        viewsets.register(chooser_viewset)

        SNIPPET_MODELS.append(model)
        SNIPPET_MODELS.sort(key=lambda x: x._meta.verbose_name)

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
        f"wagtailsnippets_{self._meta.app_label}_{self._meta.model_name}:usage",
        args=[quote(self.pk)],
    )


@classmethod
def get_admin_base_path(cls):
    return f"snippets/{cls._meta.app_label}/{cls._meta.model_name}"


@classmethod
def get_admin_url_namespace(cls):
    return f"wagtailsnippets_{cls._meta.app_label}_{cls._meta.model_name}"
