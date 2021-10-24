import os

from django.core.checks import Error, Tags, Warning, register
from django.core.exceptions import FieldDoesNotExist


@register('staticfiles')
def css_install_check(app_configs, **kwargs):
    errors = []

    css_path = os.path.join(
        os.path.dirname(__file__), 'static', 'wagtailadmin', 'css', 'normalize.css'
    )

    if not os.path.isfile(css_path):
        error_hint = """
            Most likely you are running a development (non-packaged) copy of
            Wagtail and have not built the static assets -
            see https://docs.wagtail.io/en/latest/contributing/developing.html

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


@register(Tags.admin)
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


@register(Tags.admin)
def get_form_class_check(app_configs, **kwargs):
    from wagtail.admin.forms import WagtailAdminPageForm
    from wagtail.core.models import get_page_models

    errors = []

    for cls in get_page_models():
        edit_handler = cls.get_edit_handler()
        if not issubclass(edit_handler.get_form_class(), WagtailAdminPageForm):
            errors.append(Error(
                "{cls}.get_edit_handler().get_form_class() does not extend WagtailAdminPageForm".format(
                    cls=cls.__name__),
                hint="Ensure that the EditHandler for {cls} creates a subclass of WagtailAdminPageForm".format(
                    cls=cls.__name__),
                obj=cls,
                id='wagtailadmin.E002'))

    return errors


@register('panels')
def inline_panel_model_panels_check(app_configs, **kwargs):
    from wagtail.core.models import get_page_models

    errors = []
    page_models = get_page_models()

    for cls in page_models:
        errors.extend(check_panels_in_model(cls))

    # filter out duplicate errors found for the same model
    unique_errors = []
    for error in errors:
        if error.msg not in [e.msg for e in unique_errors]:
            unique_errors.append(error)
    return unique_errors


def check_panels_in_model(cls, context='model'):
    """Check panels configuration uses `panels` when `edit_handler` not in use."""
    from wagtail.admin.edit_handlers import BaseCompositeEditHandler, InlinePanel
    from wagtail.core.models import Page

    errors = []

    if hasattr(cls, 'get_edit_handler'):
        # must check the InlinePanel related models
        edit_handler = cls.get_edit_handler()
        for tab in edit_handler.children:
            if isinstance(tab, BaseCompositeEditHandler):
                inline_panel_children = [
                    panel for panel in tab.children if isinstance(panel, InlinePanel)]
                for inline_panel_child in inline_panel_children:
                    errors.extend(check_panels_in_model(
                        inline_panel_child.db_field.related_model,
                        context='InlinePanel model',
                    ))

    if issubclass(cls, Page) or hasattr(cls, 'edit_handler'):
        # Pages do not need to be checked for standalone tabbed_panel usage
        # if edit_handler is used on any model, assume config is correct
        return errors

    tabbed_panels = [
        'content_panels',
        'promote_panels',
        'settings_panels',
    ]

    for panel_name in tabbed_panels:
        class_name = cls.__name__
        if not hasattr(cls, panel_name):
            continue

        panel_name_short = panel_name.replace('_panels', '').title()
        error_title = "{}.{} will have no effect on {} editing".format(
            class_name, panel_name, context)

        if 'InlinePanel' in context:
            error_hint = """Ensure that {} uses `panels` instead of `{}`.
There are no tabs on non-Page model editing within InlinePanels.""".format(
                class_name, panel_name)
        else:
            error_hint = """Ensure that {} uses `panels` instead of `{}`\
or set up an `edit_handler` if you want a tabbed editing interface.
There are no default tabs on non-Page models so there will be no \
{} tab for the {} to render in.""".format(
                class_name, panel_name, panel_name_short, panel_name)

        error = Warning(
            error_title,
            hint=error_hint,
            obj=cls,
            id='wagtailadmin.W002'
        )

        errors.append(error)

    return errors


@register('panels')
def panel_type_check(app_configs, **kwargs):
    from wagtail.core.models import get_page_models

    errors = []

    for cls in get_page_models():
        errors += traverse_edit_handlers(cls.get_edit_handler())

    return errors


def traverse_edit_handlers(edit_handler):
    errors = []

    try:
        for child in edit_handler.children:
            errors += traverse_edit_handlers(child)
    except AttributeError:
        error = check_stream_field_panel_type(edit_handler)
        if error:
            errors.append(error)

    return errors


def check_stream_field_panel_type(edit_handler):
    from wagtail.admin.edit_handlers import StreamFieldPanel
    from wagtail.core.fields import StreamField

    try:
        db_field = getattr(edit_handler, 'db_field', None)
        if isinstance(db_field, StreamField) and not isinstance(edit_handler, StreamFieldPanel):
            return Warning(
                "{model}.{field_name} is a StreamField, but uses {edit_handler}".format(
                    model=edit_handler.model.__name__,
                    field_name=edit_handler.field_name,
                    edit_handler=edit_handler.__class__.__name__),
                hint="Ensure that it uses a StreamFieldPanel, or change the field type",
                obj=edit_handler.model,
                id='wagtailadmin.W003'
            )
    except FieldDoesNotExist:
        # Doesn't check any fields not on the model, such as in
        # wagtail.tests.testapp.modelsFormClassAdditionalFieldPage
        pass
