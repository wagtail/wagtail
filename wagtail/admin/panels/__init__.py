from django import forms
from django.apps import apps
from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from wagtail.admin.forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES,
    FORM_FIELD_OVERRIDES,
)
from wagtail.admin.forms.pages import WagtailAdminPageForm
from wagtail.models import Page
from wagtail.utils.decorators import cached_classmethod

from .base import *  # NOQA
from .comment_panel import *  # NOQA
from .comment_panel import CommentPanel
from .deprecated import *  # NOQA
from .field_panel import *  # NOQA
from .field_panel import FieldPanel
from .group import *  # NOQA
from .group import MultiFieldPanel, ObjectList, TabbedInterface
from .help_panel import *  # NOQA
from .inline_panel import *  # NOQA
from .model_utils import *  # NOQA
from .model_utils import get_edit_handler
from .page_chooser_panel import *  # NOQA
from .publishing_panel import *  # NOQA
from .publishing_panel import PublishingPanel


# Now that we've defined panels, we can set up wagtailcore.Page to have some.
def set_default_page_edit_handlers(cls):
    cls.content_panels = [
        FieldPanel(
            "title",
            classname="title",
            widget=forms.TextInput(
                attrs={
                    "placeholder": format_lazy(
                        "{title}*", title=gettext_lazy("Page title")
                    )
                }
            ),
        ),
    ]

    cls.promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug"),
                FieldPanel("seo_title"),
                FieldPanel("search_description"),
            ],
            gettext_lazy("For search engines"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("show_in_menus"),
            ],
            gettext_lazy("For site menus"),
        ),
    ]

    cls.settings_panels = [
        PublishingPanel(),
    ]

    if getattr(settings, "WAGTAILADMIN_COMMENTS_ENABLED", True):
        cls.settings_panels.append(CommentPanel())

    cls.base_form_class = WagtailAdminPageForm


set_default_page_edit_handlers(Page)


@cached_classmethod
def _get_page_edit_handler(cls):
    """
    Get the panel to use in the Wagtail admin when editing this page type.
    """
    if hasattr(cls, "edit_handler"):
        edit_handler = cls.edit_handler
    else:
        # construct a TabbedInterface made up of content_panels, promote_panels
        # and settings_panels, skipping any which are empty
        tabs = []

        if cls.content_panels:
            tabs.append(ObjectList(cls.content_panels, heading=gettext_lazy("Content")))
        if cls.promote_panels:
            tabs.append(ObjectList(cls.promote_panels, heading=gettext_lazy("Promote")))
        if cls.settings_panels:
            tabs.append(
                ObjectList(cls.settings_panels, heading=gettext_lazy("Settings"))
            )

        edit_handler = TabbedInterface(tabs, base_form_class=cls.base_form_class)

    return edit_handler.bind_to_model(cls)


Page.get_edit_handler = _get_page_edit_handler


@receiver(setting_changed)
def reset_edit_handler_cache(**kwargs):
    """
    Clear page edit handler cache when global WAGTAILADMIN_COMMENTS_ENABLED settings are changed
    """
    if kwargs["setting"] == "WAGTAILADMIN_COMMENTS_ENABLED":
        set_default_page_edit_handlers(Page)
        for model in apps.get_models():
            if issubclass(model, Page):
                model.get_edit_handler.cache_clear()
        get_edit_handler.cache_clear()
