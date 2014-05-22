from django.db import models
from django.utils import timezone
from django.dispatch.dispatcher import receiver
from wagtail.wagtailsearch.views import search_view_served

import datetime
import string


class Query(models.Model):
    query_string = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        # Normalise query string
        self.query_string = self.normalise_query_string(self.query_string)

        super(Query, self).save(*args, **kwargs)

    def add_hit(self, date=None):
        if date is None:
            date = timezone.now().date()
        daily_hits, created = QueryDailyHits.objects.get_or_create(query=self, date=date)
        daily_hits.hits = models.F('hits') + 1
        daily_hits.save()

    def __unicode__(self):
        return self.query_string

    @property
    def hits(self):
        hits = self.daily_hits.aggregate(models.Sum('hits'))['hits__sum']
        return hits if hits else 0

    @classmethod
    def garbage_collect(cls):
        """
        Deletes all Query records that have no daily hits or editors picks
        """
        cls.objects.filter(daily_hits__isnull=True, editors_picks__isnull=True).delete()

    @classmethod
    def get(cls, query_string):
        return cls.objects.get_or_create(query_string=cls.normalise_query_string(query_string))[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        # TODO: Implement date_since
        return cls.objects.filter(daily_hits__isnull=False).annotate(_hits=models.Sum('daily_hits__hits')).distinct().order_by('-_hits')

    @staticmethod
    def normalise_query_string(query_string):
        # Convert query_string to lowercase
        query_string = query_string.lower()

        # Strip punctuation characters
        query_string = ''.join([c for c in query_string if c not in string.punctuation])

        # Remove double spaces
        query_string = ' '.join(query_string.split())

        return query_string


class QueryDailyHits(models.Model):
    query = models.ForeignKey(Query, db_index=True, related_name='daily_hits')
    date = models.DateField()
    hits = models.IntegerField(default=0)

    @classmethod
    def garbage_collect(cls):
        """
        Deletes all QueryDailyHits records that are older than 7 days
        """
        min_date = timezone.now().date() - datetime.timedelta(days=7)

        cls.objects.filter(date__lt=min_date).delete()

    class Meta:
        unique_together = (
            ('query', 'date'),
        )


@receiver(search_view_served)
def add_query_hit(request, query_string, **kwargs):
    if query_string:
        # Get query and add a hit
        query = Query.get(query_string).add_hit()


class EditorsPick(models.Model):
    query = models.ForeignKey(Query, db_index=True, related_name='editors_picks')
    page = models.ForeignKey('wagtailcore.Page', related_name='+')
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('sort_order', )
