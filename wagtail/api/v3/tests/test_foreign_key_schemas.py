from typing import get_args
from unittest import mock

from django.db import models
from django.test import TestCase
from django.test.utils import isolate_apps

from wagtail.api import APIField
from wagtail.api.v3.schemas import read_generator
from wagtail.api.v3.schemas.generators.read import SchemaGenerator
from wagtail.models import get_page_models
from wagtail.test.utils import Page


class TestForeignKeyCycles(TestCase):
    """
    A foreign key back to a model whose foreign key schema is already being
    built is expanded as a reference (primary key and meta.type), rather than
    recursing forever.
    """

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

    def test_foreign_key_to_same_model(self):
        with mock.patch.object(Page, "api_fields", [APIField("alias_of")], create=True):
            schema = self.get_generator().get_foreign_key_schema(Page)

        alias_of_schema = get_args(schema.model_fields["alias_of"].annotation)[0]
        self.assertEqual(alias_of_schema.__name__, "PageForeignKeyReferenceSchema")
        self.assertEqual(list(alias_of_schema.model_fields), ["meta", "id"])

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
        self.assertEqual(
            latest_article_schema.__name__,
            "ArticlePageForeignKeyReferenceSchema",
        )
        self.assertEqual(list(latest_article_schema.model_fields), ["meta", "id"])
        self.assertIs(
            latest_article_schema.model_fields["meta"].annotation,
            schema.model_fields["meta"].annotation,
        )
