from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailSnippetsTestsAppConfig(AppConfig):
    name = 'wagtail.tests.snippets'
    label = 'snippetstests'
    verbose_name = "Wagtail snippets tests"
