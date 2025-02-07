from django.db import models


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = "sort_order"

    class Meta:
        abstract = True
        ordering = ["sort_order"]


def set_max_order(instance, sort_order_field):
    # Get the maximum value, defaulting to 0 if no records exist
    aggregate = instance.__class__._default_manager.aggregate(
        max_order=models.Max(sort_order_field)
    )
    max_order = aggregate["max_order"] or 0
    setattr(instance, sort_order_field, max_order + 1)
    instance.save(update_fields=[sort_order_field])
