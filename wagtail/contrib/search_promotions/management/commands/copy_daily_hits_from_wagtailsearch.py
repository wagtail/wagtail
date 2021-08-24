from django.core.management.base import BaseCommand

from wagtail.contrib.search_promotions import models
from wagtail.search import models as search_models


class Command(BaseCommand):
    def handle(self, **options):
        # Queries
        self.stdout.write("Copying query records from wagtailsearch")

        models.Query.objects.bulk_create(
            [
                models.Query(query_string=query.query_string)
                for query in search_models.Query.objects.all()
            ],
            ignore_conflicts=True,
        )

        # Query daily hits
        self.stdout.write("Copying query daily hits records from wagtailsearch")

        daily_hits_list = search_models.QueryDailyHits.objects.all().select_related(
            "query"
        )

        # Prefetch referenced Query objects from the new model
        new_queries = models.Query.objects.in_bulk(
            [daily_hits.query.query_string for daily_hits in daily_hits_list],
            field_name="query_string",
        )

        # Bulk insert new daily hits records
        models.QueryDailyHits.objects.bulk_create(
            [
                models.QueryDailyHits(
                    query=new_queries[daily_hits.query.query_string],
                    date=daily_hits.date,
                    hits=daily_hits.hits,
                )
                for daily_hits in daily_hits_list
            ],
            ignore_conflicts=True,
        )
