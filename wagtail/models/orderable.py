from django.db import models


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = "sort_order"

    class Meta:
        abstract = True
        ordering = ["sort_order"]
