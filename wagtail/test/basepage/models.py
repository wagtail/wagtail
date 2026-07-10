from django.db import models

from wagtail.models import AbstractPage


class BasePage(AbstractPage):
    importance = models.CharField(max_length=255, blank=True, null=True)

    promote_panels = AbstractPage.promote_panels + ["importance"]
