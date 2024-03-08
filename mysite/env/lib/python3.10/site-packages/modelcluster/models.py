from __future__ import unicode_literals

import json
import datetime

from django.core.exceptions import FieldDoesNotExist
from django.db import models, transaction
from django.db.models.fields.related import ForeignObjectRel
from django.utils.encoding import is_protected_type
from django.core.serializers.json import DjangoJSONEncoder
from django.conf import settings
from django.utils import timezone

from modelcluster.fields import ParentalKey, ParentalManyToManyField


def get_field_value(field, model):
    if field.remote_field is None:
        value = field.pre_save(model, add=model.pk is None)

        # Make datetimes timezone aware
        # https://github.com/django/django/blob/master/django/db/models/fields/__init__.py#L1394-L1403
        if isinstance(value, datetime.datetime) and settings.USE_TZ:
            if timezone.is_naive(value):
                default_timezone = timezone.get_default_timezone()
                value = timezone.make_aware(value, default_timezone).astimezone(datetime.timezone.utc)
            else:
                # convert to UTC
                value = timezone.localtime(value, datetime.timezone.utc)

        if is_protected_type(value):
            return value
        else:
            return field.value_to_string(model)
    else:
        return getattr(model, field.get_attname())


def get_serializable_data_for_fields(model):
    """
    Return a serialised version of the model's fields which exist as local database
    columns (i.e. excluding m2m and incoming foreign key relations)
    """
    pk_field = model._meta.pk
    # If model is a child via multitable inheritance, use parent's pk
    while pk_field.remote_field and pk_field.remote_field.parent_link:
        pk_field = pk_field.remote_field.model._meta.pk

    obj = {'pk': get_field_value(pk_field, model)}

    for field in model._meta.fields:
        if field.serialize:
            obj[field.name] = get_field_value(field, model)

    return obj


def model_from_serializable_data(model, data, check_fks=True, strict_fks=False):
    pk_field = model._meta.pk
    kwargs = {}

    # If model is a child via multitable inheritance, we need to set ptr_id fields all the way up
    # to the main PK field, as Django won't populate these for us automatically.
    while pk_field.remote_field and pk_field.remote_field.parent_link:
        kwargs[pk_field.attname] = data['pk']
        pk_field = pk_field.remote_field.model._meta.pk

    kwargs[pk_field.attname] = data['pk']

    for field_name, field_value in data.items():
        try:
            field = model._meta.get_field(field_name)
        except FieldDoesNotExist:
            continue

        # Filter out reverse relations
        if isinstance(field, ForeignObjectRel):
            continue

        if field.remote_field and isinstance(field.remote_field, models.ManyToManyRel):
            related_objects = field.remote_field.model._default_manager.filter(pk__in=field_value)
            kwargs[field.attname] = list(related_objects)

        elif field.remote_field and isinstance(field.remote_field, models.ManyToOneRel):
            if field_value is None:
                kwargs[field.attname] = None
            else:
                clean_value = field.remote_field.model._meta.get_field(field.remote_field.field_name).to_python(field_value)
                kwargs[field.attname] = clean_value
                if check_fks:
                    try:
                        field.remote_field.model._default_manager.get(**{field.remote_field.field_name: clean_value})
                    except field.remote_field.model.DoesNotExist:
                        if field.remote_field.on_delete == models.DO_NOTHING:
                            pass
                        elif field.remote_field.on_delete == models.CASCADE:
                            if strict_fks:
                                return None
                            else:
                                kwargs[field.attname] = None

                        elif field.remote_field.on_delete == models.SET_NULL:
                            kwargs[field.attname] = None

                        else:
                            raise Exception("can't currently handle on_delete types other than CASCADE, SET_NULL and DO_NOTHING")
        else:
            value = field.to_python(field_value)

            # Make sure datetimes are converted to localtime
            if isinstance(field, models.DateTimeField) and settings.USE_TZ and value is not None:
                default_timezone = timezone.get_default_timezone()
                if timezone.is_aware(value):
                    value = timezone.localtime(value, default_timezone)
                else:
                    value = timezone.make_aware(value, default_timezone)

            kwargs[field.name] = value

    obj = model(**kwargs)

    if data['pk'] is not None:
        # Set state to indicate that this object has come from the database, so that
        # ModelForm validation doesn't try to enforce a uniqueness check on the primary key
        obj._state.adding = False

    return obj


def get_all_child_relations(model):
    """
    Return a list of RelatedObject records for child relations of the given model,
    including ones attached to ancestors of the model
    """
    return [
        field for field in model._meta.get_fields()
        if isinstance(field.remote_field, ParentalKey)
    ]


def get_all_child_m2m_relations(model):
    """
    Return a list of ParentalManyToManyFields on the given model,
    including ones attached to ancestors of the model
    """
    return [
        field for field in model._meta.get_fields()
        if isinstance(field, ParentalManyToManyField)
    ]


class ClusterableModel(models.Model):
    def __init__(self, *args, **kwargs):
        """
        Extend the standard model constructor to allow child object lists to be passed in
        via kwargs
        """
        child_relation_names = (
            [rel.get_accessor_name() for rel in get_all_child_relations(self)] +
            [field.name for field in get_all_child_m2m_relations(self)]
        )

        if any(name in kwargs for name in child_relation_names):
            # One or more child relation values is being passed in the constructor; need to
            # separate these from the standard field kwargs to be passed to 'super'
            kwargs_for_super = kwargs.copy()
            relation_assignments = {}
            for rel_name in child_relation_names:
                if rel_name in kwargs:
                    relation_assignments[rel_name] = kwargs_for_super.pop(rel_name)

            super().__init__(*args, **kwargs_for_super)
            for (field_name, related_instances) in relation_assignments.items():
                setattr(self, field_name, related_instances)
        else:
            super().__init__(*args, **kwargs)

    def save(self, **kwargs):
        """
        Save the model and commit all child relations.
        """
        child_relation_names = [rel.get_accessor_name() for rel in get_all_child_relations(self)]
        child_m2m_field_names = [field.name for field in get_all_child_m2m_relations(self)]

        update_fields = kwargs.pop('update_fields', None)
        if update_fields is None:
            real_update_fields = None
            relations_to_commit = child_relation_names
            m2m_fields_to_commit = child_m2m_field_names
        else:
            real_update_fields = []
            relations_to_commit = []
            m2m_fields_to_commit = []
            for field in update_fields:
                if field in child_relation_names:
                    relations_to_commit.append(field)
                elif field in child_m2m_field_names:
                    m2m_fields_to_commit.append(field)
                else:
                    real_update_fields.append(field)

        super().save(update_fields=real_update_fields, **kwargs)

        for relation in relations_to_commit:
            getattr(self, relation).commit()

        for field in m2m_fields_to_commit:
            getattr(self, field).commit()

    def serializable_data(self):
        obj = get_serializable_data_for_fields(self)

        for rel in get_all_child_relations(self):
            rel_name = rel.get_accessor_name()
            children = getattr(self, rel_name).all()

            if hasattr(rel.related_model, 'serializable_data'):
                obj[rel_name] = [child.serializable_data() for child in children]
            else:
                obj[rel_name] = [get_serializable_data_for_fields(child) for child in children]

        for field in get_all_child_m2m_relations(self):
            if field.serialize:
                children = getattr(self, field.name).all()
                obj[field.name] = [child.pk for child in children]

        return obj

    def to_json(self):
        return json.dumps(self.serializable_data(), cls=DjangoJSONEncoder)

    @classmethod
    def from_serializable_data(cls, data, check_fks=True, strict_fks=False):
        """
        Build an instance of this model from the JSON-like structure passed in,
        recursing into related objects as required.
        If check_fks is true, it will check whether referenced foreign keys still
        exist in the database.
        - dangling foreign keys on related objects are dealt with by either nullifying the key or
        dropping the related object, according to the 'on_delete' setting.
        - dangling foreign keys on the base object will be nullified, unless strict_fks is true,
        in which case any dangling foreign keys with on_delete=CASCADE will cause None to be
        returned for the entire object.
        """
        obj = model_from_serializable_data(cls, data, check_fks=check_fks, strict_fks=strict_fks)
        if obj is None:
            return None

        child_relations = get_all_child_relations(cls)

        for rel in child_relations:
            rel_name = rel.get_accessor_name()
            try:
                child_data_list = data[rel_name]
            except KeyError:
                continue

            related_model = rel.related_model
            if hasattr(related_model, 'from_serializable_data'):
                children = [
                    related_model.from_serializable_data(child_data, check_fks=check_fks, strict_fks=True)
                    for child_data in child_data_list
                ]
            else:
                children = [
                    model_from_serializable_data(related_model, child_data, check_fks=check_fks, strict_fks=True)
                    for child_data in child_data_list
                ]

            children = filter(lambda child: child is not None, children)

            setattr(obj, rel_name, children)

        return obj

    @classmethod
    def from_json(cls, json_data, check_fks=True, strict_fks=False):
        return cls.from_serializable_data(json.loads(json_data), check_fks=check_fks, strict_fks=strict_fks)

    @transaction.atomic
    def copy_child_relation(self, child_relation, target, commit=False, append=False):
        """
        Copies all of the objects in the accessor_name to the target object.

        For example, say we have an event with speakers (my_event) and we need to copy these to another event (my_other_event):

            my_event.copy_child_relation('speakers', my_other_event)

        By default, this copies the child objects without saving them. Set the commit paremter to True to save the objects
        but note that this would cause an exception if the target object is not saved.

        This will overwrite the child relation on the target object. This is to avoid any issues with unique keys
        and/or sort_order. If you want it to append. set the `append` parameter to True.

        This method returns a dictionary mapping the child relation/primary key on the source object to the new object created for the
        target object.
        """
        # A dict that maps child objects from their old IDs to their new objects
        child_object_map = {}

        if isinstance(child_relation, str):
            child_relation = self._meta.get_field(child_relation)

        if not isinstance(child_relation.remote_field, ParentalKey):
            raise LookupError("copy_child_relation can only be used for relationships defined with a ParentalKey")

        # The name of the ParentalKey field on the child model
        parental_key_name = child_relation.field.attname

        # Get managers for both the source and target objects
        source_manager = getattr(self, child_relation.get_accessor_name())
        target_manager = getattr(target, child_relation.get_accessor_name())

        if not append:
            target_manager.clear()

        for child_object in source_manager.all().order_by('pk'):
            old_pk = child_object.pk
            is_saved = old_pk is not None
            child_object.pk = None
            setattr(child_object, parental_key_name, target.id)
            target_manager.add(child_object)

            # Add mapping to object
            # If the PK is none, add them into a list since there may be multiple of these
            if old_pk is not None:
                child_object_map[(child_relation, old_pk)] = child_object
            else:
                if (child_relation, None) not in child_object_map:
                    child_object_map[(child_relation, None)] = []

                child_object_map[(child_relation, None)].append(child_object)

        if commit:
            target_manager.commit()

        return child_object_map

    def copy_all_child_relations(self, target, exclude=None, commit=False, append=False):
        """
        Copies all of the objects in all child relations to the target object.

        This will overwrite all of the child relations on the target object.

        Set exclude to a list of child relation accessor names that shouldn't be copied.

        This method returns a dictionary mapping the child_relation/primary key on the source object to the new object created for the
        target object.
        """
        exclude = exclude or []
        child_object_map = {}

        for child_relation in get_all_child_relations(self):
            if child_relation.get_accessor_name() in exclude:
                continue

            child_object_map.update(self.copy_child_relation(child_relation, target, commit=commit, append=append))

        return child_object_map

    def copy_cluster(self, exclude_fields=None):
        """
        Makes a copy of this object and all child relations.

        Includes all field data including child relations and parental many to many fields.

        Doesn't include non-parental many to many.

        The result of this method is unsaved.
        """
        exclude_fields = exclude_fields or []

        # Extract field data from self into a dictionary
        data_dict = {}
        for field in self._meta.get_fields():
            # Ignore explicitly excluded fields
            if field.name in exclude_fields:
                continue

            # Ignore reverse relations
            if field.auto_created:
                continue

            # Copy parental m2m relations
            # Otherwise add them to the m2m dict to be set after saving
            if field.many_to_many:
                if isinstance(field, ParentalManyToManyField):
                    parental_field = getattr(self, field.name)
                    if hasattr(parental_field, 'all'):
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
                data_dict[field.attname] = getattr(self, field.attname)

            else:
                data_dict[field.name] = getattr(self, field.name)

        # Create copy
        copy = self.__class__(**data_dict)

        # Copy child relations
        child_object_map = self.copy_all_child_relations(copy, exclude=exclude_fields)

        return copy, child_object_map

    class Meta:
        abstract = True
