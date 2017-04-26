# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from wagtail.tests.search.models import SearchTest
from wagtail.wagtailsearch.tests.test_backends import BackendTests


class TestPostgresBackend(BackendTests, TestCase):
    backend_path = 'wagtail.contrib.wagtailpostgressearch.backend'

    def test_unaccent(self):
        self.backend.reset_index()

        # Add some test data
        obj = SearchTest()
        obj.title = "Ĥéllø"
        obj.live = True
        obj.save()
        self.backend.add(obj)

        # Search and check
        results = self.backend.search("Hello", SearchTest.objects.all())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, obj.id)
