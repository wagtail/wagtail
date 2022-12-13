from django import forms
from django.conf import settings
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy

from wagtail.admin.forms.pages import WagtailAdminPageForm
from wagtail.models import Page
from wagtail.utils.decorators import cached_classmethod

from .comment_panel import CommentPanel
from .field_panel import FieldPanel
from .group import MultiFieldPanel, ObjectList, TabbedInterface
from .publishing_panel import PublishingPanel


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
