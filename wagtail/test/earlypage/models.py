# This module DOES NOT import from wagtail.admin -
# this tests that we are able to define Page models before wagtail.admin is loaded.

from django.db import models

from wagtail.models import Page


class EarlyPage(Page):
    intro = models.TextField(blank=True)

    content_panels = Page.content_panels + [
        "intro",
    ]
