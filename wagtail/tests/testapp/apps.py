from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailTestsAppConfig(AppConfig):
    name = 'wagtail.tests.testapp'
    label = 'tests'
    verbose_name = "Wagtail tests"
