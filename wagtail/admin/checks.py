import os

from django.core.checks import Error, Warning, register


@register()
def css_install_check(app_configs, **kwargs):
    errors = []

    css_path = os.path.join(
        os.path.dirname(__file__), 'static', 'wagtailadmin', 'css', 'normalize.css'
    )

    if not os.path.isfile(css_path):
        error_hint = """
            Most likely you are running a development (non-packaged) copy of
            Wagtail and have not built the static assets -
            see http://docs.wagtail.io/en/latest/contributing/developing.html

            File not found: %s
        """ % css_path

        errors.append(
            Warning(
                "CSS for the Wagtail admin is missing",
                hint=error_hint,
                id='wagtailadmin.W001',
            )
        )
    return errors


@register()
def base_form_class_check(app_configs, **kwargs):
    from wagtail.admin.forms import WagtailAdminPageForm
    from wagtail.core.models import get_page_models

    errors = []

    for cls in get_page_models():
        if not issubclass(cls.base_form_class, WagtailAdminPageForm):
            errors.append(Error(
                "{}.base_form_class does not extend WagtailAdminPageForm".format(
                    cls.__name__),
                hint="Ensure that {}.{} extends WagtailAdminPageForm".format(
                    cls.base_form_class.__module__,
                    cls.base_form_class.__name__),
                obj=cls,
                id='wagtailadmin.E001'))

    return errors


@register()
def get_form_class_check(app_configs, **kwargs):
    from wagtail.admin.edit_handlers import BaseInlinePanel
    from wagtail.admin.forms import WagtailAdminPageForm
    from wagtail.core.models import get_page_models

    errors = []

    checked_models = []

    for cls in get_page_models():
        edit_handler = cls.get_edit_handler()
        form_class = edit_handler.get_form_class(cls)
        if not issubclass(form_class, WagtailAdminPageForm):
            errors.append(Error(
                "{cls}.get_edit_handler().get_form_class({cls}) does not extend WagtailAdminPageForm".format(
                    cls=cls.__name__),
                hint="Ensure that the EditHandler for {cls} creates a subclass of WagtailAdminPageForm".format(
                    cls=cls.__name__),
                obj=cls,
                id='wagtailadmin.E002'))
        for tab in edit_handler.children:
            for panel in [p for p in tab.children if issubclass(p, BaseInlinePanel)]:
                inline_panel_model = panel.related.related_model
                if inline_panel_model not in checked_models:
                    errors += check_panel_config(
                        inline_panel_model,
                        context='InlinePanel model',
                    )
                    checked_models.append(inline_panel_model)

    return errors


def check_panel_config(cls, context='model'):
    """Check panels configuration uses `panels` when `edit_handler` not in use."""

    errors = []
    panels = [
        'content_panels',
        'promote_panels',
        'settings_panels',
    ]

    if hasattr(cls, 'edit_handler'):
        # assume configuration is correct if edit_handler is in use
        return errors

    for panel in panels:
        if not hasattr(cls, panel):
            continue
        name = cls.__name__
        tab = panel.replace('_panels', '').title()
        if 'InlinePanel' in context:
            error_hint = """Ensure that {} uses `panels` instead of `{}`.
        There are no tabs on non-Page model editing within InlinePanels.
        """.format(name, panel, tab, panel)
        else:
            error_hint = """Ensure that {} uses `panels` instead of `{}`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        {} tab for the {} to render in.""".format(name, panel, tab, panel)

        error = Warning(
            "{}.{} will have no effect on {} editing".format(name, panel, context),
            hint=error_hint,
            obj=cls,
            id='wagtailadmin.W002'
        )
        errors.append(error)

    return errors
