from django.test import TestCase

from wagtail.search import index
from wagtail.test.search.models import Book, Novel
from wagtail.test.testapp.models import Advert, ManyToManyBlogPage


class TestSelectOnQuerySet(TestCase):
    def test_select_on_queryset_with_foreign_key(self):
        fields = index.RelatedFields(
            "protagonist",
            [
                index.SearchField("name"),
            ],
        )

        queryset = fields.select_on_queryset(Novel.objects.all())

        # ForeignKey should be select_related
        self.assertFalse(queryset._prefetch_related_lookups)
        self.assertIn("protagonist", queryset.query.select_related)

    def test_select_on_queryset_with_one_to_one(self):
        fields = index.RelatedFields(
            "book_ptr",
            [
                index.SearchField("title"),
            ],
        )

        queryset = fields.select_on_queryset(Novel.objects.all())

        # OneToOneField should be select_related
        self.assertFalse(queryset._prefetch_related_lookups)
        self.assertIn("book_ptr", queryset.query.select_related)

    def test_select_on_queryset_with_many_to_many(self):
        fields = index.RelatedFields(
            "adverts",
            [
                index.SearchField("title"),
            ],
        )

        queryset = fields.select_on_queryset(ManyToManyBlogPage.objects.all())

        # ManyToManyField should be prefetch_related
        self.assertIn("adverts", queryset._prefetch_related_lookups)
        self.assertFalse(queryset.query.select_related)

    def test_select_on_queryset_with_reverse_foreign_key(self):
        fields = index.RelatedFields(
            "categories", [index.RelatedFields("category", [index.SearchField("name")])]
        )

        queryset = fields.select_on_queryset(ManyToManyBlogPage.objects.all())

        # reverse ForeignKey should be prefetch_related
        self.assertIn("categories", queryset._prefetch_related_lookups)
        self.assertFalse(queryset.query.select_related)

    def test_select_on_queryset_with_reverse_one_to_one(self):
        fields = index.RelatedFields(
            "novel",
            [
                index.SearchField("subtitle"),
            ],
        )

        queryset = fields.select_on_queryset(Book.objects.all())

        # reverse OneToOneField should be select_related
        self.assertFalse(queryset._prefetch_related_lookups)
        self.assertIn("novel", queryset.query.select_related)

    def test_select_on_queryset_with_reverse_many_to_many(self):
        fields = index.RelatedFields(
            "manytomanyblogpage",
            [
                index.SearchField("title"),
            ],
        )

        queryset = fields.select_on_queryset(Advert.objects.all())

        # reverse ManyToManyField should be prefetch_related
        self.assertIn("manytomanyblogpage", queryset._prefetch_related_lookups)
        self.assertFalse(queryset.query.select_related)

    def test_select_on_queryset_with_taggable_manager(self):
        fields = index.RelatedFields(
            "tags",
            [
                index.SearchField("name"),
            ],
        )

        queryset = fields.select_on_queryset(Novel.objects.all())

        # Tags should be prefetch_related
        self.assertIn("tags", queryset._prefetch_related_lookups)
        self.assertFalse(queryset.query.select_related)
