from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig


class WagtailSearchTestsAppConfig(AppConfig):
    name = 'wagtail.tests.search'
    label = 'searchtests'
    verbose_name = "Wagtail search tests"
