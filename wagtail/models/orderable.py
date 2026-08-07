from django.core import checks
from django.db import models


class Orderable(models.Model):
    sort_order = models.IntegerField(null=True, blank=True, editable=False)
    sort_order_field = "sort_order"

    class Meta:
        abstract = True
        ordering = ["sort_order"]

    @classmethod
    def check(cls, **kwargs):
        errors = super().check(**kwargs)

        meta_attr = cls._meta.original_attrs
        ordering = cls._meta.ordering or []
        ordering_defined = "ordering" in meta_attr

        # Scenario - 1
        # Developer added a class Meta for an unrelated reason (e.g. verbose_name),
        # now needs to add Orderable.Meta
        if not ordering_defined and "sort_order" not in ordering:
            errors.append(
                checks.Warning(
                    "{0}.{1} inherits from Orderable, but its Meta does not inherit "
                    "Orderable.Meta, so ordering is lost.".format(
                        cls._meta.app_label, cls.__name__
                    ),
                    hint="Add Orderable.Meta as parent class to {}.Meta".format(
                        cls.__name__
                    ),
                    obj=cls,
                    id="wagtailcore.W002",
                )
            )
            return errors

        # Scenario - 2
        # Developer added a class Meta (with or without the Orderable.Meta) with the
        # intention of overriding ordering, now needs to add 'sort_order' back
        if "sort_order" not in ordering:
            errors.append(
                checks.Warning(
                    "{0}.{1} inherits from Orderable, but "
                    "{1}.Meta.ordering does not include 'sort_order'".format(
                        cls._meta.app_label, cls.__name__
                    ),
                    hint="Add 'sort_order' to {}.Meta.ordering.".format(cls.__name__),
                    obj=cls,
                    id="wagtailcore.W003",
                )
            )
        return errors


def set_max_order(instance, sort_order_field):
    # Get the maximum value, defaulting to 0 if no records exist
    aggregate = instance.__class__._default_manager.aggregate(
        max_order=models.Max(sort_order_field)
    )
    max_order = aggregate["max_order"] or 0
    setattr(instance, sort_order_field, max_order + 1)
    instance.save(update_fields=[sort_order_field])
