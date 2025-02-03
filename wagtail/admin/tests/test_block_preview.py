from django.contrib.auth.models import Permission
from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from wagtail import blocks
from wagtail.test.utils import WagtailTestUtils


class TestStreamFieldBlockPreviewView(WagtailTestUtils, TestCase):
    def get(self, block):
        return self.client.get(
            reverse("wagtailadmin_block_preview"),
            {"id": block.definition_prefix},
        )

    def setUp(self):
        self.user = self.login()

    def test_simple(self):
        block = blocks.CharBlock(
            label="Single-line text",
            description="A single line of text",
            preview_value="Hello, world!",
        )
        block.set_name("single_line_text")
        response = self.get(block)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        html = soup.select_one("html")
        self.assertIsNotNone(html)
        self.assertEqual(html["lang"], "en")
        self.assertEqual(html["dir"], "ltr")

        robots = soup.select_one("meta[name=robots]")
        self.assertIsNotNone(robots)
        self.assertEqual(robots["content"], "noindex")

        title = soup.select_one("title")
        self.assertIsNotNone(title)
        self.assertEqual(title.text.strip(), "Preview for Single-line text (CharBlock)")

        main = soup.select_one("main")
        self.assertIsNotNone(main)
        self.assertEqual(main.text.strip(), "Hello, world!")

        wrapper = main.select_one("div.block-single_line_text")
        self.assertIsNotNone(wrapper)

    def test_nonexisting_block(self):
        response = self.client.get(reverse("wagtailadmin_block_preview"))
        self.assertEqual(response.status_code, 404)

        response = self.client.get(
            reverse("wagtailadmin_block_preview"),
            {"id": "nonexisting"},
        )
        self.assertEqual(response.status_code, 404)

    def test_no_admin_permission(self):
        self.user.is_superuser = False
        self.user.save()

        block = blocks.CharBlock()
        response = self.get(block)
        self.assertRedirects(
            response,
            reverse("wagtailadmin_login")
            + "?"
            + urlencode({"next": response.wsgi_request.get_full_path()}),
        )

    def test_minimal_permission(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin",
                codename="access_admin",
            )
        )
        self.user.save()

        block = blocks.CharBlock(preview_value="Hello, world!")
        response = self.get(block)
        self.assertEqual(response.status_code, 200)

    def test_no_preview_value_no_default(self):
        block = blocks.Block()
        response = self.get(block)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        self.assertIsNotNone(main)
        self.assertEqual(main.text.strip(), "None")

    def test_preview_value_falls_back_to_default(self):
        block = blocks.IntegerBlock(default=42)
        response = self.get(block)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        self.assertIsNotNone(main)
        self.assertEqual(main.text.strip(), "42")

    def test_preview_template(self):
        class PreviewTemplateViaMeta(blocks.Block):
            class Meta:
                preview_template = "tests/custom_block_preview.html"

        class PreviewTemplateViaMethod(blocks.Block):
            def get_preview_template(self, value=None, context=None):
                return "tests/custom_block_preview.html"

        cases = [
            ("meta", PreviewTemplateViaMeta()),
            ("method", PreviewTemplateViaMethod()),
            ("kwarg", blocks.Block(preview_template="tests/custom_block_preview.html")),
        ]

        for via, block in cases:
            with self.subTest(via=via):
                response = self.get(block)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "tests/custom_block_preview.html")

                response = self.get(block)
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(response, "tests/custom_block_preview.html")

                soup = self.get_soup(response.content)
                custom_wrapper = soup.select_one("main .my-preview-wrapper")
                self.assertIsNotNone(custom_wrapper)

                custom_css = soup.select_one("link[rel=stylesheet]")
                self.assertIsNotNone(custom_css)
                self.assertEqual(custom_css["href"], "/static/css/custom.css")

                custom_js = soup.select_one("script[src]")
                self.assertIsNotNone(custom_js)
                self.assertEqual(custom_js["src"], "/static/js/custom.js")

    def test_preview_value(self):
        class PreviewValueViaMeta(blocks.Block):
            class Meta:
                preview_value = "Hello, world!"

        class PreviewValueViaMethod(blocks.Block):
            def get_preview_value(self):
                return "Hello, world!"

        cases = [
            ("meta", PreviewValueViaMeta()),
            ("method", PreviewValueViaMethod()),
            ("kwarg", blocks.Block(preview_value="Hello, world!")),
        ]

        for via, block in cases:
            with self.subTest(via=via):
                response = self.get(block)
                self.assertEqual(response.status_code, 200)
                soup = self.get_soup(response.content)
                main = soup.select_one("main")
                self.assertIsNotNone(main)
                self.assertEqual(main.text.strip(), "Hello, world!")

    def test_custom_preview_context(self):
        preview_value = "With a custom context"
        label = "Fancy block"

        class CustomPreviewContextBlock(blocks.Block):
            def get_preview_context(block, value, parent_context=None):
                self.assertEqual(value, preview_value)
                self.assertIsNotNone(parent_context)
                self.assertIsInstance(parent_context.get("request"), HttpRequest)
                self.assertIs(parent_context.get("block_def"), block)
                self.assertIs(
                    parent_context.get("block_class"),
                    CustomPreviewContextBlock,
                )
                self.assertIsInstance(
                    parent_context.get("bound_block"),
                    blocks.BoundBlock,
                )
                self.assertEqual(
                    parent_context.get("page_title"),
                    "Preview for Fancy block (CustomPreviewContextBlock)",
                )
                return {
                    **parent_context,
                    "extra": "Added by get_preview_context",
                    "page_title": "Custom title",
                }

        block = CustomPreviewContextBlock(label=label, preview_value=preview_value)
        response = self.get(block)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        main = soup.select_one("main")
        self.assertIsNotNone(main)
        self.assertEqual(main.text.strip(), preview_value)
        # Ensure custom context can add and override values
        self.assertEqual(response.context["extra"], "Added by get_preview_context")
        self.assertEqual(response.context["page_title"], "Custom title")
        # Ensure that the default context is still present
        self.assertIs(response.context["block_def"], block)

    def test_static_image_preview(self):
        class StaticImagePreviewBlock(blocks.Block):
            def get_preview_context(self, value, parent_context=None):
                return {
                    "image_path": "block_previews/preview.jpg",
                    "image_description": "A preview of the block",
                }

            class Meta:
                preview_template = "tests/static_block_preview.html"

        block = StaticImagePreviewBlock()
        response = self.get(block)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tests/static_block_preview.html")
        soup = self.get_soup(response.content)
        img = soup.select_one("html body main img")
        self.assertIsNotNone(img)
        self.assertEqual(img["src"], "/static/block_previews/preview.jpg")
        self.assertEqual(img["alt"], "A preview of the block")
