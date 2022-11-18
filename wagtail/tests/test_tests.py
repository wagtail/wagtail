import json

from django.test import TestCase

from wagtail.admin.tests.test_contentstate import content_state_equal
from wagtail.models import PAGE_MODEL_CLASSES, Page, Site
from wagtail.test.testapp.models import (
    BusinessChild,
    BusinessIndex,
    BusinessNowherePage,
    BusinessSubIndex,
    EventIndex,
    EventPage,
    SectionedRichTextPage,
    SimpleChildPage,
    SimplePage,
    SimpleParentPage,
    StreamPage,
)
from wagtail.test.utils import WagtailPageTests, WagtailTestUtils
from wagtail.test.utils.form_data import (
    inline_formset,
    nested_form_data,
    rich_text,
    streamfield,
)


class TestAssertTagInHTML(WagtailTestUtils, TestCase):
    def test_assert_tag_in_html(self):
        haystack = """<ul>
            <li class="normal">hugh</li>
            <li class="normal">pugh</li>
            <li class="really important" lang="en"><em>barney</em> mcgrew</li>
        </ul>"""
        self.assertTagInHTML('<li lang="en" class="important really">', haystack)
        self.assertTagInHTML('<li class="normal">', haystack, count=2)

        with self.assertRaises(AssertionError):
            self.assertTagInHTML('<div lang="en" class="important really">', haystack)
        with self.assertRaises(AssertionError):
            self.assertTagInHTML(
                '<li lang="en" class="important really">', haystack, count=2
            )
        with self.assertRaises(AssertionError):
            self.assertTagInHTML('<li lang="en" class="important">', haystack)
        with self.assertRaises(AssertionError):
            self.assertTagInHTML(
                '<li lang="en" class="important really" data-extra="boom">', haystack
            )

    def test_assert_tag_in_html_with_extra_attrs(self):
        haystack = """<ul>
            <li class="normal">hugh</li>
            <li class="normal">pugh</li>
            <li class="really important" lang="en"><em>barney</em> mcgrew</li>
        </ul>"""
        self.assertTagInHTML(
            '<li class="important really">', haystack, allow_extra_attrs=True
        )
        self.assertTagInHTML("<li>", haystack, count=3, allow_extra_attrs=True)

        with self.assertRaises(AssertionError):
            self.assertTagInHTML(
                '<li class="normal" lang="en">', haystack, allow_extra_attrs=True
            )
        with self.assertRaises(AssertionError):
            self.assertTagInHTML(
                '<li class="important really">',
                haystack,
                count=2,
                allow_extra_attrs=True,
            )

    def test_assert_tag_in_template_script(self):
        haystack = """<html>
            <script type="text/template">
                <p class="really important">first template block</p>
            </script>
            <script type="text/template">
                <p class="really important">second template block</p>
            </script>
            <p class="normal">not in a script tag</p>
        </html>"""

        self.assertTagInTemplateScript('<p class="important really">', haystack)
        self.assertTagInTemplateScript(
            '<p class="important really">', haystack, count=2
        )

        with self.assertRaises(AssertionError):
            self.assertTagInTemplateScript('<p class="normal">', haystack)


class TestWagtailPageTests(WagtailPageTests):
    def setUp(self):
        super().setUp()
        site = Site.objects.get(is_default_site=True)
        self.root = site.root_page.specific

    def test_assert_can_create_at(self):
        # It should be possible to create an EventPage under an EventIndex,
        self.assertCanCreateAt(EventIndex, EventPage)
        self.assertCanCreateAt(Page, EventIndex)
        # It should not be possible to create a SimplePage under a BusinessChild
        self.assertCanNotCreateAt(SimplePage, BusinessChild)

        # This should raise, as it *is not* possible
        with self.assertRaises(AssertionError):
            self.assertCanCreateAt(SimplePage, BusinessChild)
        # This should raise, as it *is* possible
        with self.assertRaises(AssertionError):
            self.assertCanNotCreateAt(EventIndex, EventPage)

    def test_assert_can_create(self):
        self.assertFalse(EventIndex.objects.exists())
        self.assertCanCreate(
            self.root,
            EventIndex,
            {
                "title": "Event Index",
                "intro": """{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "Event intro", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}""",
            },
        )
        self.assertTrue(EventIndex.objects.exists())

        self.assertCanCreate(
            self.root,
            StreamPage,
            {
                "title": "Flierp",
                "body-0-type": "text",
                "body-0-value": "Dit is onze mooie text",
                "body-0-order": "0",
                "body-0-deleted": "",
                "body-1-type": "rich_text",
                "body-1-value": """{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "Dit is onze mooie text in een ferrari", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}""",
                "body-1-order": "1",
                "body-1-deleted": "",
                "body-2-type": "product",
                "body-2-value-name": "pegs",
                "body-2-value-price": "a pound",
                "body-2-order": "2",
                "body-2-deleted": "",
                "body-count": "3",
            },
        )

        self.assertCanCreate(
            self.root,
            SectionedRichTextPage,
            {
                "title": "Fight Club",
                "sections-TOTAL_FORMS": "2",
                "sections-INITIAL_FORMS": "0",
                "sections-MIN_NUM_FORMS": "0",
                "sections-MAX_NUM_FORMS": "1000",
                "sections-0-body": """{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "Rule 1: You do not talk about Fight Club", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}""",
                "sections-0-ORDER": "0",
                "sections-0-DELETE": "",
                "sections-1-body": """{"entityMap": {},"blocks": [
                {"inlineStyleRanges": [], "text": "Rule 2: You DO NOT talk about Fight Club", "depth": 0, "type": "unstyled", "key": "00000", "entityRanges": []}
            ]}""",
                "sections-1-ORDER": "0",
                "sections-1-DELETE": "",
            },
        )

    def test_assert_can_create_for_page_with_publish(self):
        self.assertCanCreate(
            self.root,
            SimplePage,
            {"title": "Simple Lorem Page", "content": "Lorem ipsum dolor sit amet"},
            publish=True,
        )

    def test_assert_can_create_with_form_helpers(self):
        # same as test_assert_can_create, but using the helpers from wagtail.test.utils.form_data
        # as an end-to-end test
        self.assertFalse(EventIndex.objects.exists())
        self.assertCanCreate(
            self.root,
            EventIndex,
            nested_form_data(
                {"title": "Event Index", "intro": rich_text("<p>Event intro</p>")}
            ),
        )
        self.assertTrue(EventIndex.objects.exists())

        self.assertCanCreate(
            self.root,
            StreamPage,
            nested_form_data(
                {
                    "title": "Flierp",
                    "body": streamfield(
                        [
                            ("text", "Dit is onze mooie text"),
                            (
                                "rich_text",
                                rich_text(
                                    "<p>Dit is onze mooie text in een ferrari</p>"
                                ),
                            ),
                            ("product", {"name": "pegs", "price": "a pound"}),
                        ]
                    ),
                }
            ),
        )

        self.assertCanCreate(
            self.root,
            SectionedRichTextPage,
            nested_form_data(
                {
                    "title": "Fight Club",
                    "sections": inline_formset(
                        [
                            {
                                "body": rich_text(
                                    "<p>Rule 1: You do not talk about Fight Club</p>"
                                )
                            },
                            {
                                "body": rich_text(
                                    "<p>Rule 2: You DO NOT talk about Fight Club</p>"
                                )
                            },
                        ]
                    ),
                }
            ),
        )

    def test_assert_can_create_subpage_rules(self):
        simple_page = SimplePage(title="Simple Page", slug="simple", content="hello")
        self.root.add_child(instance=simple_page)
        # This should raise an error, as a BusinessChild can not be created under a SimplePage
        with self.assertRaisesRegex(
            AssertionError,
            r"Can not create a tests.businesschild under a tests.simplepage",
        ):
            self.assertCanCreate(simple_page, BusinessChild, {})

    def test_assert_can_create_validation_error(self):
        # This should raise some validation errors, complaining about missing
        # title and slug fields
        with self.assertRaisesRegex(AssertionError, r"\bslug:\n[\s\S]*\btitle:\n"):
            self.assertCanCreate(self.root, SimplePage, {})

    def test_assert_allowed_subpage_types(self):
        self.assertAllowedSubpageTypes(BusinessIndex, {BusinessChild, BusinessSubIndex})
        self.assertAllowedSubpageTypes(BusinessChild, {})
        # All page types can be created under the Page model, except those with a parent_page_types
        # rule excluding it
        all_but_business = set(PAGE_MODEL_CLASSES) - {
            BusinessSubIndex,
            BusinessChild,
            BusinessNowherePage,
            SimpleChildPage,
        }
        self.assertAllowedSubpageTypes(Page, all_but_business)
        with self.assertRaises(AssertionError):
            self.assertAllowedSubpageTypes(
                BusinessSubIndex, {BusinessSubIndex, BusinessChild}
            )

    def test_assert_allowed_parent_page_types(self):
        self.assertAllowedParentPageTypes(
            BusinessChild, {BusinessIndex, BusinessSubIndex}
        )
        self.assertAllowedParentPageTypes(BusinessSubIndex, {BusinessIndex})
        # BusinessIndex can be created under all page types that do not have a subpage_types rule
        all_but_business = set(PAGE_MODEL_CLASSES) - {
            BusinessSubIndex,
            BusinessChild,
            BusinessIndex,
            SimpleParentPage,
        }
        self.assertAllowedParentPageTypes(BusinessIndex, all_but_business)
        with self.assertRaises(AssertionError):
            self.assertAllowedParentPageTypes(
                BusinessSubIndex, {BusinessSubIndex, BusinessIndex}
            )


class TestFormDataHelpers(TestCase):
    def test_nested_form_data(self):
        result = nested_form_data(
            {
                "foo": "bar",
                "parent": {
                    "child": "field",
                },
            }
        )
        self.assertEqual(result, {"foo": "bar", "parent-child": "field"})

    def test_streamfield(self):
        result = nested_form_data(
            {
                "content": streamfield(
                    [
                        ("text", "Hello, world"),
                        ("text", "Goodbye, world"),
                        ("coffee", {"type": "latte", "milk": "soya"}),
                    ]
                )
            }
        )

        self.assertEqual(
            result,
            {
                "content-count": "3",
                "content-0-type": "text",
                "content-0-value": "Hello, world",
                "content-0-order": "0",
                "content-0-deleted": "",
                "content-1-type": "text",
                "content-1-value": "Goodbye, world",
                "content-1-order": "1",
                "content-1-deleted": "",
                "content-2-type": "coffee",
                "content-2-value-type": "latte",
                "content-2-value-milk": "soya",
                "content-2-order": "2",
                "content-2-deleted": "",
            },
        )

    def test_inline_formset(self):
        result = nested_form_data(
            {
                "lines": inline_formset(
                    [
                        {"text": "Hello"},
                        {"text": "World"},
                    ]
                )
            }
        )

        self.assertEqual(
            result,
            {
                "lines-TOTAL_FORMS": "2",
                "lines-INITIAL_FORMS": "0",
                "lines-MIN_NUM_FORMS": "0",
                "lines-MAX_NUM_FORMS": "1000",
                "lines-0-text": "Hello",
                "lines-0-ORDER": "0",
                "lines-0-DELETE": "",
                "lines-1-text": "World",
                "lines-1-ORDER": "1",
                "lines-1-DELETE": "",
            },
        )

    def test_default_rich_text(self):
        result = rich_text("<h2>title</h2><p>para</p>")
        self.assertTrue(
            content_state_equal(
                json.loads(result),
                {
                    "entityMap": {},
                    "blocks": [
                        {
                            "inlineStyleRanges": [],
                            "text": "title",
                            "depth": 0,
                            "type": "header-two",
                            "key": "00000",
                            "entityRanges": [],
                        },
                        {
                            "inlineStyleRanges": [],
                            "text": "para",
                            "depth": 0,
                            "type": "unstyled",
                            "key": "00000",
                            "entityRanges": [],
                        },
                    ],
                },
            )
        )

    def test_rich_text_with_custom_features(self):
        # feature list doesn't allow <h2>, so it should become an unstyled paragraph block
        result = rich_text("<h2>title</h2><p>para</p>", features=["p"])
        self.assertTrue(
            content_state_equal(
                json.loads(result),
                {
                    "entityMap": {},
                    "blocks": [
                        {
                            "inlineStyleRanges": [],
                            "text": "title",
                            "depth": 0,
                            "type": "unstyled",
                            "key": "00000",
                            "entityRanges": [],
                        },
                        {
                            "inlineStyleRanges": [],
                            "text": "para",
                            "depth": 0,
                            "type": "unstyled",
                            "key": "00000",
                            "entityRanges": [],
                        },
                    ],
                },
            )
        )

    def test_rich_text_with_alternative_editor(self):
        result = rich_text("<h2>title</h2><p>para</p>", editor="custom")
        self.assertEqual(result, "<h2>title</h2><p>para</p>")
