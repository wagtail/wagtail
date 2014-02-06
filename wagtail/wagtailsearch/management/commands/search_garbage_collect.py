from django.core.management.base import NoArgsCommand

from wagtail.wagtailsearch import models


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        # Clean daily hits
        print "Cleaning daily hits records... ",
        models.QueryDailyHits.garbage_collect()
        print "Done"

        # Clean queries
        print "Cleaning query records... ",
        models.Query.garbage_collect()
        print "Done"
