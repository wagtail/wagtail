import logging

import factory
from django.utils.text import slugify
from factory import errors, utils
from factory.declarations import ParameteredAttribute
from factory.django import DjangoModelFactory

from wagtail.documents import get_document_model
from wagtail.images import get_image_model
from wagtail.models import Collection, Page, Site

__all__ = [
    "CollectionFactory",
    "ImageFactory",
    "PageFactory",
    "SiteFactory",
    "DocumentFactory",
]
logger = logging.getLogger(__file__)


class ParentNodeFactory(ParameteredAttribute):

    EXTEND_CONTAINERS = True
    FORCE_SEQUENCE = False
    UNROLL_CONTEXT_BEFORE_EVALUATION = False

    def generate(self, step, params):
        if not params:
            return None

        subfactory = step.builder.factory_meta.factory
        logger.debug(
            "ParentNodeFactory: Instantiating %s.%s(%s), create=%r",
            subfactory.__module__,
            subfactory.__name__,
            utils.log_pprint(kwargs=params),
            step,
        )
        force_sequence = step.sequence if self.FORCE_SEQUENCE else None
        return step.recurse(subfactory, params, force_sequence=force_sequence)


class MP_NodeFactory(DjangoModelFactory):

    parent = ParentNodeFactory()

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        kwargs.pop("parent")
        return model_class(**kwargs)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        parent = kwargs.pop("parent")

        if cls._meta.django_get_or_create:
            instance = cls._get_or_create(model_class, *args, parent=parent, **kwargs)
        else:
            instance = cls._create_instance(model_class, parent, kwargs)
            assert instance.pk
        return instance

    @classmethod
    def _create_instance(cls, model_class, parent, kwargs):
        instance = model_class(**kwargs)
        if parent:
            parent.add_child(instance=instance)
        else:
            model_class.add_root(instance=instance)
        return instance

    @classmethod
    def _get_or_create(cls, model_class, *args, **kwargs):
        """Create an instance of the model through objects.get_or_create."""
        manager = cls._get_manager(model_class)
        assert "defaults" not in cls._meta.django_get_or_create, (
            "'defaults' is a reserved keyword for get_or_create "
            "(in %s._meta.django_get_or_create=%r)"
            % (cls, cls._meta.django_get_or_create)
        )

        lookup_fields = {}
        for field in cls._meta.django_get_or_create:
            if field not in kwargs:
                raise errors.FactoryError(
                    "django_get_or_create - "
                    "Unable to find initialization value for '%s' in factory %s"
                    % (field, cls.__name__)
                )
            lookup_fields[field] = kwargs[field]

        parent = lookup_fields.pop("parent", None)
        kwargs.pop("parent", None)

        if parent:
            try:
                return manager.child_of(parent).get(**lookup_fields)
            except model_class.DoesNotExist:
                return cls._create_instance(model_class, parent, kwargs)
        else:
            return super()._get_or_create(model_class, *args, **kwargs)


class CollectionFactory(MP_NodeFactory):
    name = "Test collection"

    class Meta:
        model = Collection


class PageFactory(MP_NodeFactory):
    title = "Test page"
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))

    class Meta:
        model = Page


class CollectionMemberFactory(DjangoModelFactory):
    collection = factory.SubFactory(CollectionFactory, parent=None)


class ImageFactory(CollectionMemberFactory):
    class Meta:
        model = get_image_model()

    title = "An image"
    file = factory.django.ImageField()


class SiteFactory(DjangoModelFactory):
    hostname = "localhost"
    port = factory.Sequence(lambda n: 81 + n)
    site_name = "Test site"
    root_page = factory.SubFactory(PageFactory, parent=None)
    is_default_site = False

    class Meta:
        model = Site


class DocumentFactory(CollectionMemberFactory):
    class Meta:
        model = get_document_model()

    title = "A document"
    file = factory.django.FileField()
