from __future__ import absolute_import, unicode_literals

import datetime

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailsearch.utils import MAX_QUERY_STRING_LENGTH, normalise_query_string


@python_2_unicode_compatible
class Query(models.Model):
    query_string = models.CharField(max_length=MAX_QUERY_STRING_LENGTH, unique=True)

    def save(self, *args, **kwargs):
        # Normalise query string
        self.query_string = normalise_query_string(self.query_string)

        super(Query, self).save(*args, **kwargs)

    def add_hit(self, date=None):
        if date is None:
            date = timezone.now().date()
        daily_hits, created = QueryDailyHits.objects.get_or_create(query=self, date=date)
        daily_hits.hits = models.F('hits') + 1
        daily_hits.save()

    def __str__(self):
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
        return cls.objects.get_or_create(query_string=normalise_query_string(query_string))[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        # TODO: Implement date_since
        return (cls.objects.filter(daily_hits__isnull=False)
                .annotate(_hits=models.Sum('daily_hits__hits'))
                .distinct().order_by('-_hits'))


class QueryDailyHits(models.Model):
    query = models.ForeignKey(Query, db_index=True, related_name='daily_hits', on_delete=models.CASCADE)
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
        verbose_name = _('Query Daily Hits')
