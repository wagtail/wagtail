import datetime

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from wagtail.search.utils import MAX_QUERY_STRING_LENGTH, normalise_query_string


class Query(models.Model):
    query_string = models.CharField(max_length=MAX_QUERY_STRING_LENGTH, unique=True)

    def save(self, *args, **kwargs):
        # Normalise query string
        self.query_string = normalise_query_string(self.query_string)

        super().save(*args, **kwargs)

    def add_hit(self, date=None):
        if date is None:
            date = timezone.now().date()
        daily_hits, created = QueryDailyHits.objects.get_or_create(
            query=self, date=date
        )
        daily_hits.hits = models.F("hits") + 1
        daily_hits.save()

    def __str__(self):
        return self.query_string

    @property
    def hits(self):
        hits = self.daily_hits.aggregate(models.Sum("hits"))["hits__sum"]
        return hits if hits else 0

    @classmethod
    def garbage_collect(cls):
        """
        Deletes all Query records that have no daily hits or editors picks
        """
        extra_filter_kwargs = (
            {
                "editors_picks__isnull": True,
            }
            if hasattr(cls, "editors_picks")
            else {}
        )
        cls.objects.filter(daily_hits__isnull=True, **extra_filter_kwargs).delete()

    @classmethod
    def get(cls, query_string):
        return cls.objects.get_or_create(
            query_string=normalise_query_string(query_string)
        )[0]

    @classmethod
    def get_most_popular(cls, date_since=None):
        objects = cls.objects.filter(daily_hits__isnull=False)

        if date_since:
            objects = objects.filter(daily_hits__date__gte=date_since)

        return (
            objects.annotate(_hits=models.Sum("daily_hits__hits"))
            .distinct()
            .order_by("-_hits")
        )


class QueryDailyHits(models.Model):
    query = models.ForeignKey(
        Query, db_index=True, related_name="daily_hits", on_delete=models.CASCADE
    )
    date = models.DateField()
    hits = models.IntegerField(default=0)

    @classmethod
    def garbage_collect(cls, days=None):
        """
        Deletes all QueryDailyHits records that are older than a set number of days
        """
        days = (
            getattr(settings, "WAGTAILSEARCH_HITS_MAX_AGE", 7) if days is None else days
        )
        min_date = timezone.now().date() - datetime.timedelta(days)

        cls.objects.filter(date__lt=min_date).delete()

    class Meta:
        unique_together = (("query", "date"),)
        verbose_name = _("Query Daily Hits")
        verbose_name_plural = _("Query Daily Hits")


class SearchPromotion(models.Model):
    query = models.ForeignKey(
        Query, db_index=True, related_name="editors_picks", on_delete=models.CASCADE
    )
    page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("page"),
        help_text=_("Choose an internal page for this promotion"),
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    external_link_url = models.URLField(
        _("External link URL"),
        help_text=_("Alternatively, use an external link for this promotion"),
        blank=True,
    )
    external_link_text = models.CharField(
        max_length=200,
        blank=True,
        null=True,
    )
    description = models.TextField(
        verbose_name=_("description"),
        help_text=_("Applies to internal page or external link"),
        blank=True,
    )
    sort_order = models.IntegerField(null=True, blank=True, editable=False)

    @property
    def title(self):
        if self.page:
            prop = self.page.title
        else:
            prop = self.external_link_text
        return prop

    @property
    def link(self):
        if self.page:
            prop = self.page
        else:
            prop = self.external_link_url
        return prop

    def __repr__(self):
        if self.page:
            label = "page"
        else:
            label = "external link"

        return f'SearchPromotion(query="{self.query.query_string}", {label}="{self.title}")'

    def __str__(self):
        return f"{self.query.query_string} - {self.title}"

    class Meta:
        ordering = ("sort_order",)
        verbose_name = _("search promotion")
