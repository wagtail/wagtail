from typing import get_args
from unittest import mock

from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.api import APIField
from wagtail.api.v3.schemas import BasePageSchema, BaseSchema, read_generator
from wagtail.api.v3.schemas.generators.read import SchemaGenerator
from wagtail.api.v3.schemas.pages import SimpleBasePageSchema
from wagtail.models import Orderable, get_page_models
from wagtail.test.utils import Page


class SchemaGeneratorTestCase(TestCase):
    def setUp(self):
        # Page models defined in the tests are added to PAGE_MODEL_CLASSES,
        # which isolate_apps doesn't undo. Use a copy so they don't leak into
        # other tests that rely on the list of page models.
        self.enterContext(
            mock.patch("wagtail.models.pages.PAGE_MODEL_CLASSES", get_page_models())
        )

    def get_generator(self):
        generator = SchemaGenerator()
        generator.field_schemas = dict(read_generator.field_schemas)
        return generator


class TestForeignKeyCycles(SchemaGeneratorTestCase):
    """
    A foreign key back to a model whose foreign key schema is already being
    built is expanded as a reference (primary key and meta.type, or the same
    as meta.parent for a page), rather than recursing forever.
    """

    def test_foreign_key_to_same_model(self):
        with mock.patch.object(Page, "api_fields", [APIField("alias_of")], create=True):
            schema = self.get_generator().get_foreign_key_schema(Page)

        self.assertEqual(schema.__name__, f"{Page._meta.object_name}ForeignKeySchema")
        self.assertEqual(set(schema.model_fields), {"meta", "id", "title", "alias_of"})
        alias_of_schema = get_args(schema.model_fields["alias_of"].annotation)[0]
        self.assertIs(alias_of_schema, SimpleBasePageSchema)

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def test_foreign_keys_between_models(self):
        class TestsMeta:
            app_label = "tests"

        class ArticlePage(Page):
            author = models.ForeignKey("Author", on_delete=models.SET_NULL, null=True)
            api_fields = [APIField("author")]
            Meta = TestsMeta

        class Author(models.Model):
            latest_article = models.ForeignKey(ArticlePage, on_delete=models.CASCADE)
            api_fields = [APIField("latest_article")]
            Meta = TestsMeta

        schema = self.get_generator().get_foreign_key_schema(ArticlePage)

        author = schema.model_fields["author"]
        author_schema = get_args(author.annotation)[0]
        self.assertEqual(author_schema.__name__, "AuthorForeignKeySchema")
        latest_article = author_schema.model_fields["latest_article"]
        latest_article_schema = latest_article.annotation
        self.assertEqual(latest_article_schema.__name__, "SimpleBasePageSchema")
        self.assertEqual(
            list(latest_article_schema.model_fields),
            ["meta", "id", "title"],
        )
        self.assertIs(
            latest_article_schema.model_fields["meta"].annotation,
            schema.model_fields["meta"].annotation,
        )

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def test_reference_to_multi_level_subclass(self):
        class TestsMeta:
            app_label = "tests"

        class Place(models.Model):
            Meta = TestsMeta

        class Restaurant(Place):
            Meta = TestsMeta

        class Bistro(Restaurant):
            Meta = TestsMeta

        schema = self.get_generator().get_foreign_key_reference_schema(Bistro)

        # The primary key is the root model's (id), rather than the parent
        # links (restaurant_ptr or place_ptr)
        self.assertEqual(schema.__name__, "BistroForeignKeyReferenceSchema")
        self.assertEqual(list(schema.model_fields), ["meta", "id"])


class TestChildRelationParentalKeys(SchemaGeneratorTestCase):
    """
    A child relation's ParentalKey back to the object it's nested in is
    expanded as a reference, rather than repeating the whole object in every
    item.
    """

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def test_parental_key_to_page(self):
        class TestsMeta:
            app_label = "tests"

        class ArticlePage(Page):
            introduction = models.TextField()
            api_fields = [APIField("introduction"), APIField("related_links")]
            Meta = TestsMeta

        class EventPage(ArticlePage):
            Meta = TestsMeta

        class ArticleRelatedLink(Orderable):
            page = ParentalKey(
                ArticlePage, related_name="related_links", on_delete=models.CASCADE
            )
            link_page = models.ForeignKey(
                ArticlePage, related_name="+", on_delete=models.CASCADE
            )
            api_fields = [APIField("page"), APIField("link_page")]
            Meta = TestsMeta

        for model in [ArticlePage, EventPage]:
            with self.subTest(model=model.__name__):
                schema = self.get_generator().generate_schema(
                    model, base_class=BasePageSchema
                )

                related_links = schema.model_fields["related_links"]
                link_schema = get_args(related_links.annotation)[0]
                self.assertIs(
                    link_schema.model_fields["page"].annotation,
                    SimpleBasePageSchema,
                )
                # A foreign key to another page of the same type is still
                # expanded with the page's api_fields
                link_page_schema = link_schema.model_fields["link_page"].annotation
                self.assertEqual(
                    link_page_schema.__name__, "ArticlePageForeignKeySchema"
                )
                self.assertIn("introduction", link_page_schema.model_fields)

    @isolate_apps("wagtail.test.testapp", "wagtail")
    def test_parental_key_to_non_page_model(self):
        class TestsMeta:
            app_label = "tests"

        class Menu(ClusterableModel):
            name = models.CharField(max_length=255)
            api_fields = [APIField("name"), APIField("items")]
            Meta = TestsMeta

        class MenuItem(Orderable):
            menu = ParentalKey(Menu, related_name="items", on_delete=models.CASCADE)
            label = models.CharField(max_length=255)
            api_fields = [APIField("menu"), APIField("label")]
            Meta = TestsMeta

        schema = self.get_generator().generate_schema(Menu, base_class=BaseSchema)

        item_schema = get_args(schema.model_fields["items"].annotation)[0]
        menu_schema = item_schema.model_fields["menu"].annotation
        self.assertEqual(menu_schema.__name__, "MenuForeignKeyReferenceSchema")
        self.assertEqual(list(menu_schema.model_fields), ["meta", "id"])
