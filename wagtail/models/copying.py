from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel


def _extract_field_data(source, exclude_fields=None):
    """
    Get dictionaries representing the model's field data.

    This excludes many to many fields (which are handled by _copy_m2m_relations)'
    """
    exclude_fields = exclude_fields or []
    data_dict = {}

    for field in source._meta.get_fields():
        # Ignore explicitly excluded fields
        if field.name in exclude_fields:
            continue

        # Ignore reverse relations
        if field.auto_created:
            continue

        # Ignore reverse generic relations
        if isinstance(field, GenericRelation):
            continue

        # Copy parental m2m relations
        if field.many_to_many:
            if isinstance(field, ParentalManyToManyField):
                parental_field = getattr(source, field.name)
                if hasattr(parental_field, "all"):
                    values = parental_field.all()
                    if values:
                        data_dict[field.name] = values
            continue

        # Ignore parent links (page_ptr)
        if isinstance(field, models.OneToOneField) and field.remote_field.parent_link:
            continue

        if isinstance(field, models.ForeignKey):
            # Use attname to copy the ID instead of retrieving the instance

            # Note: We first need to set the field to None to unset any object
            # that's there already just setting _id on its own won't change the
            # field until its saved.

            data_dict[field.name] = None
            data_dict[field.attname] = getattr(source, field.attname)

        else:
            data_dict[field.name] = getattr(source, field.name)

    return data_dict


def _copy_m2m_relations(source, target, exclude_fields=None, update_attrs=None):
    """
    Copies non-ParentalManyToMany m2m relations
    """
    update_attrs = update_attrs or {}
    exclude_fields = exclude_fields or []

    for field in source._meta.get_fields():
        # Copy m2m relations. Ignore explicitly excluded fields, reverse relations, and Parental m2m fields.
        if (
            field.many_to_many
            and field.name not in exclude_fields
            and not field.auto_created
            and not isinstance(field, ParentalManyToManyField)
        ):
            try:
                # Do not copy m2m links with a through model that has a ParentalKey to the model being copied - these will be copied as child objects
                through_model_parental_links = [
                    field
                    for field in field.through._meta.get_fields()
                    if isinstance(field, ParentalKey)
                    and issubclass(source.__class__, field.related_model)
                ]
                if through_model_parental_links:
                    continue
            except AttributeError:
                pass

            if field.name in update_attrs:
                value = update_attrs[field.name]

            else:
                value = getattr(source, field.name).all()

            getattr(target, field.name).set(value)


def _copy(source, exclude_fields=None, update_attrs=None):
    data_dict = _extract_field_data(source, exclude_fields=exclude_fields)
    target = source.__class__(**data_dict)

    if update_attrs:
        for field, value in update_attrs.items():
            if field not in data_dict:
                continue
            setattr(target, field, value)

    if isinstance(source, ClusterableModel):
        child_object_map = source.copy_all_child_relations(
            target, exclude=exclude_fields
        )
    else:
        child_object_map = {}

    return target, child_object_map
