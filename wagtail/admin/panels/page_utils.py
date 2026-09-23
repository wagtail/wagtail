from django.utils.translation import gettext_lazy

from wagtail.utils.decorators import cached_classmethod

from .group import ObjectList, TabbedInterface


@cached_classmethod
def _get_page_edit_handler_tabs(cls):
    """
    Build the default tab structure to use in the Wagtail admin when editing this
    page type.
    """
    tabs = []

    if cls.content_panels:
        tabs.append(ObjectList(cls.content_panels, heading=gettext_lazy("Content")))
    if cls.promote_panels:
        tabs.append(ObjectList(cls.promote_panels, heading=gettext_lazy("Promote")))
    if cls.settings_panels:
        tabs.append(
            ObjectList(cls.settings_panels, heading=gettext_lazy("Settings"))
        )

    return tabs


@cached_classmethod
def _get_page_edit_handler(cls):
    """
    Get the panel to use in the Wagtail admin when editing this page type.
    """
    if hasattr(cls, "edit_handler"):
        edit_handler = cls.edit_handler
    else:
        edit_handler = TabbedInterface(
            cls.get_edit_handler_tabs(),
            base_form_class=cls.base_form_class,
        )

    return edit_handler.bind_to_model(cls)
