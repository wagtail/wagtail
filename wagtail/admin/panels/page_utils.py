from django.conf import settings
from django.utils.translation import gettext_lazy

from wagtail.admin.widgets.slug import SlugInput
from wagtail.models import Page

from .comment_panel import CommentPanel
from .field_panel import FieldPanel
from .group import MultiFieldPanel
from .publishing_panel import PublishingPanel
from .title_field_panel import TitleFieldPanel


def set_default_page_edit_handlers(cls):
    cls.content_panels = [
        TitleFieldPanel("title"),
    ]

    cls.promote_panels = [
        MultiFieldPanel(
            [
                FieldPanel("slug", widget=SlugInput),
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


set_default_page_edit_handlers(Page)
