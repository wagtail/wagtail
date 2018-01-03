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

    for cls in get_page_models():
        edit_handler = cls.get_edit_handler()
        if not issubclass(edit_handler.get_form_class(cls), WagtailAdminPageForm):
            errors.append(Error(
                "{cls}.get_edit_handler().get_form_class({cls}) does not extend WagtailAdminPageForm".format(
                    cls=cls.__name__),
                hint="Ensure that the EditHandler for {cls} creates a subclass of WagtailAdminPageForm".format(
                    cls=cls.__name__),
                obj=cls,
                id='wagtailadmin.E002'))
        for tab in edit_handler.children:
            for panel in [p for p in tab.children if issubclass(p, BaseInlinePanel)]:
                errors += check_panel_config(
                    panel.related.related_model,
                    context='InlinePanel model'
                )

    return errors


def check_panel_config(cls, context='model'):
    """Generic check function for panel config, see usage within specific modules."""

    errors = []
    panels = [
        'content_panels',
        'promote_panels',
        'settings_panels',
    ]

    if hasattr(cls, 'edit_handler'):
        # edit_handler is checked in `get_form_class_check`
        return errors

    for panel in panels:
        if not hasattr(cls, panel):
            continue
        name = cls.__name__
        tab = panel.replace('_panels', '').title()
        error_hint = """Ensure that {} uses `panels` instead of `{}`
        or set up an `edit_handler` if you want a tabbed editing interface.
        There are no default tabs on non-Page models so there will be no
        {} tab for the {} to render in.
        """.format(name, panel, tab, panel)
        error = Warning(
            "{}.{} will have no effect on {} editing".format(name, panel, context),
            hint=error_hint,
            obj=cls,
            id='wagtailadmin.W002'
        )
        errors.append(error)

    return errors
