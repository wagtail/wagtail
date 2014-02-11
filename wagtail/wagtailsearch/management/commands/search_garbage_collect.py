from django.core.management.base import NoArgsCommand

from wagtail.wagtailsearch import models


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Clean daily hits
        self.stdout.write("Cleaning daily hits records... ")
        models.QueryDailyHits.garbage_collect()
        self.stdout.write("Done")

        # Clean queries
        self.stdout.write("Cleaning query records... ")
        models.Query.garbage_collect()
        self.stdout.write("Done")
