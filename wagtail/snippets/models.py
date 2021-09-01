from django.contrib.admin.utils import quote
from django.core import checks
from django.db.models import ForeignKey, Model
from django.urls import reverse

from wagtail.admin.admin_url_finder import register_admin_url_finder
from wagtail.admin.checks import check_panels_in_model
from wagtail.admin.forms.models import register_form_field_override
from wagtail.admin.models import get_object_usage

from .widgets import AdminSnippetChooser

SNIPPET_MODELS = []


def get_snippet_models():
    return SNIPPET_MODELS


class DefaultSnippetConfig:
    list_per_page = 20


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


def _register_snippet(model, config=DefaultSnippetConfig):
    if model not in SNIPPET_MODELS:
        model.snippet_config = config
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


def register_snippet(model=None, config=None):
    """
    A decorator to register a Model as a Snippet.
    Can be used used as a decorator with custom config kwarg.

    ```
    @register_snippet
    class FooterText(models.Model):
        pass
    ```

    ```
    class MySnippetConfig:
        per_page = 10

    @register_snippet(MySnippetConfig)
    class FooterText(models.Model):
        pass
    ```

    Allow to be called as a function, but requires both args
    class MySnippetConfig:
        per_page = 10

    class FooterText(models.Model):
        pass

    register_snippet(FooterText, MySnippetConfig)
    ```
    """

    if model is None and config is None:
        # @register_snippet()
        def dec(snippet_model):
            return _register_snippet(snippet_model)

        return dec

    elif model is not None and config is None:
        if issubclass(model, Model):
            # @register_snippet
            return _register_snippet(model)
        else:
            # @register_snippet(SomeConfig)
            # model (positional arg) is the config in this case
            def dec(snippet_model):
                return _register_snippet(snippet_model, config=model)

            return dec

    elif model is None and config is not None:
        # @register_snippet(config=SomeConfig)
        def dec(snippet_model):
            return _register_snippet(snippet_model, config=config)

        return dec

    elif config is not None and model is not None:
        # called as a function, not a decorator
        # register_snippet(SomeModel, SomeConfig)
        # or register_snippet(model=SomeModel, config=SomeConfig)
        return _register_snippet(model, config)

    else:
        raise ValueError(
            "Unsupported arguments to register_snippet: (%r, %r)" % (model, config),
        )


def get_snippet_usage_url(self):
    return reverse(
        "wagtailsnippets:usage",
        args=(self._meta.app_label, self._meta.model_name, quote(self.pk)),
    )
