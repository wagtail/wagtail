import pytest
from django import forms
from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Site, Page, Locale


class MyComponent(models.Model):
    parent = ParentalKey(
        "MySettings",
        on_delete=models.CASCADE,
        related_name="mycomponent",
        unique=True,
    )
    field1 = models.IntegerField(default=100)
    field2 = models.IntegerField(default=200)
    panels = [FieldPanel("field1"), FieldPanel("field2")]


@register_setting
class MySettings(BaseSiteSetting, ClusterableModel):
    panels = [InlinePanel("mycomponent", heading="My Component", min_num=1, max_num=1)]


# Simple ModelForm for settings (no BaseSiteSettingForm in Wagtail 7)
class MySettingsForm(forms.ModelForm):
    class Meta:
        model = MySettings
        fields = "__all__"


@pytest.mark.django_db
class TestInlinePanelDefaults:
    def test_inline_with_defaults_saves_without_changes(self):
        locale, _ = Locale.objects.get_or_create(language_code="en")
        root_page, _ = Page.objects.get_or_create(
            title="Root", slug="root", depth=1, path="0001", locale=locale
        )

        site = Site.objects.filter(is_default_site=True).first()
        if not site:
            site = Site.objects.create(
                hostname="localhost",
                root_page=root_page,
                is_default_site=True,
            )

        settings, _ = MySettings.objects.get_or_create(site=site)

        data = {
            "mycomponent-TOTAL_FORMS": "1",
            "mycomponent-INITIAL_FORMS": "0",
            "mycomponent-MIN_NUM_FORMS": "1",
            "mycomponent-MAX_NUM_FORMS": "1",
            "mycomponent-0-field1": "100",
            "mycomponent-0-field2": "200",
        }

        form = MySettingsForm(instance=settings, data=data)

        is_valid = form.is_valid()
        errors = form.errors.as_text()
        assert is_valid, f"Form should be valid but got errors: {errors}"


