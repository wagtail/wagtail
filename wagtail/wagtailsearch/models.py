from django.db import models
from django.utils import timezone

from indexed import Indexed
from searcher import Searcher
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
        return self.daily_hits.aggregate(models.Sum('hits'))['hits__sum']

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


class EditorsPick(models.Model):
    query = models.ForeignKey(Query, db_index=True, related_name='editors_picks')
    page = models.ForeignKey('wagtailcore.Page')
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('sort_order', )


# Used for tests

class SearchTest(models.Model, Indexed):
    title = models.CharField(max_length=255)
    content = models.TextField()

    indexed_fields = ("title", "content")

    title_search = Searcher(["title"])


class SearchTestChild(SearchTest):
    extra_content = models.TextField()

    indexed_fields = "extra_content"
