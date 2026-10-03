# This module DOES NOT import from wagtail.admin -
# this tests that we are able to define Page models before wagtail.admin is loaded.

import swapper
from django.db import models

# Ensure that we look at the setting WAGTAIL_PAGE_MODEL rather than WAGTAILCORE_PAGE_MODEL.
# This is set in wagtail.models, but we need to set it here too, because this module is imported first.
swapper.set_app_prefix("wagtailcore", "wagtail")

if swapper.is_swapped("wagtailcore", "Page"):
    from wagtail.test.basepage.models import BasePage as Page
else:
    from wagtail.models import Page


class EarlyPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        "intro",
    ]
