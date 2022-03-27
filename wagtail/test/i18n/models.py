from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.models import Orderable, Page, TranslatableMixin


class TestPage(Page):
    pass


class TestModel(TranslatableMixin):
    title = models.CharField(max_length=255)


class InheritedTestModel(TestModel):
    class Meta:
        unique_together = None


class TestChildObject(TranslatableMixin, Orderable):
    page = ParentalKey(TestPage, related_name="test_childobjects")
    field = models.TextField()

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass


class TestNonParentalChildObject(TranslatableMixin, Orderable):
    page = models.ForeignKey(
        TestPage, on_delete=models.CASCADE, related_name="test_nonparentalchildobjects"
    )
    field = models.TextField()


class ClusterableTestModel(TranslatableMixin, ClusterableModel):
    title = models.CharField(max_length=255)


class ClusterableTestModelChild(Orderable):
    parent = ParentalKey(
        ClusterableTestModel, on_delete=models.CASCADE, related_name="children"
    )
    field = models.TextField()


class ClusterableTestModelTranslatableChild(TranslatableMixin, Orderable):
    parent = ParentalKey(
        ClusterableTestModel,
        on_delete=models.CASCADE,
        related_name="translatable_children",
    )
    field = models.TextField()

    class Meta(TranslatableMixin.Meta, Orderable.Meta):
        pass
