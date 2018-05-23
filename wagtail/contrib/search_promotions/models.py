from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.search.models import Query


class SearchPromotion(models.Model):
    query = models.ForeignKey(Query, db_index=True, related_name='editors_picks', on_delete=models.CASCADE)
    page = models.ForeignKey('wagtailcore.Page', null=True, blank=True, verbose_name=_('page'), on_delete=models.CASCADE)
    external_page = models.URLField(blank=True, help_text='A page not on this site')
    external_page_title = models.CharField(blank=True, max_length=255, help_text='Title for a page not on this site')
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    description = models.TextField(verbose_name=_('description'), blank=True)

    def __repr__(self):
        return 'SearchPromotion(query="' + self.query.query_string + '", page="' + self.page.title + '")'

    class Meta:
        ordering = ('sort_order', )
        verbose_name = _("search promotion")
