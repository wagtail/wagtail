from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailTestsAppConfig(AppConfig):
    name = 'wagtail.tests.modeladmintest'
    label = 'test_modeladmintest'
    verbose_name = "Test Wagtail Model Admin"
