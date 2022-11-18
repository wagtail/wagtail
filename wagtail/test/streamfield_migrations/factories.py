import factory
import wagtail_factories
from factory.django import DjangoModelFactory

from . import models


class SimpleStructBlockFactory(wagtail_factories.StructBlockFactory):
    char1 = "Char Block 1"
    char2 = "Char Block 2"

    class Meta:
        model = models.SimpleStructBlock


class SimpleStreamBlockFactory(wagtail_factories.StreamBlockFactory):
    char1 = "Char Block 1"
    char2 = "Char Block 2"

    class Meta:
        model = models.SimpleStreamBlock


class NestedStructBlockFactory(wagtail_factories.StructBlockFactory):
    char1 = "Char Block 1"
    struct1 = factory.SubFactory(SimpleStructBlockFactory)
    stream1 = factory.SubFactory(SimpleStreamBlockFactory)
    list1 = wagtail_factories.ListBlockFactory(wagtail_factories.CharBlockFactory)

    class Meta:
        model = models.NestedStructBlock


class NestedStreamBlockFactory(wagtail_factories.StreamBlockFactory):
    char1 = "Char Block 1"
    struct1 = factory.SubFactory(SimpleStructBlockFactory)
    stream1 = factory.SubFactory(SimpleStreamBlockFactory)
    list1 = wagtail_factories.ListBlockFactory(wagtail_factories.CharBlockFactory)

    class Meta:
        model = models.NestedStreamBlock


class BaseStreamBlockFactory(wagtail_factories.StreamBlockFactory):
    char1 = "Char Block 1"
    char2 = "Char Block 2"
    simplestruct = factory.SubFactory(SimpleStructBlockFactory)
    simplestream = factory.SubFactory(SimpleStreamBlockFactory)
    simplelist = wagtail_factories.ListBlockFactory(wagtail_factories.CharBlockFactory)
    nestedstruct = factory.SubFactory(NestedStructBlockFactory)
    nestedstream = factory.SubFactory(NestedStreamBlockFactory)
    nestedlist_struct = wagtail_factories.ListBlockFactory(SimpleStructBlockFactory)
    nestedlist_stream = wagtail_factories.ListBlockFactory(SimpleStreamBlockFactory)

    class Meta:
        model = models.BaseStreamBlock


class SampleModelFactory(DjangoModelFactory):
    content = wagtail_factories.StreamFieldFactory(BaseStreamBlockFactory)

    class Meta:
        model = models.SampleModel


class SamplePageFactory(wagtail_factories.PageFactory):
    content = wagtail_factories.StreamFieldFactory(BaseStreamBlockFactory)

    class Meta:
        model = models.SamplePage
