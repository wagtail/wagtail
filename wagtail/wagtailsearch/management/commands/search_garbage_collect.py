from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from wagtail.wagtailsearch import models


class Command(BaseCommand):
    def handle(self, **options):
        # Clean daily hits
        self.stdout.write("Cleaning daily hits records... ")
        models.QueryDailyHits.garbage_collect()
        self.stdout.write("Done")

        # Clean queries
        self.stdout.write("Cleaning query records... ")
        models.Query.garbage_collect()
        self.stdout.write("Done")
