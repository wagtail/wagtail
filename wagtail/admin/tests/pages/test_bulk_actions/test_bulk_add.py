from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.test import TestCase
from wagtail.models import Page, BulkPageManager
from wagtail.test.testapp.models import SimplePage
from wagtail.test.utils import WagtailTestUtils


# Test normal flow
# Test auto generate slug
# Test auto generated slug has conflict with existing slug
# Test slug conflicts with another slug of a page about to be added
# Test slug conflicts with another slug of a page that already exists


class TestBulkAdd(WagtailTestUtils, TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)

        # Create child pages without slugs explicitly set
        self.child_pages = [SimplePage(title=f"Page {i}") for i in range(100)]
        # Create child pages with explicit slugs
        self.child_pages.extend(
            [SimplePage(title=f"Page {i}", slug=f"page-{i}") for i in range(100)]
        )
        self.manager = BulkPageManager(self.root_page)

    def test_bulk_add_children(self):
        # Test normal flow
        # Create a list of pages to add
        self.manager.bulk_add_children(self.child_pages)

        # Check that the pages were added
        self.assertEqual(self.root_page.get_children().count(), 200)

        # Check if the slugs were generated correctly or incremented to avoid conflicts
        for child_page in self.root_page.get_children():
            self.assertTrue(child_page.slug.startswith("page-"))
            self.assertTrue(
                child_page.slug.endswith(str(child_page.title[-1]))
                or child_page.slug.endswith(str(child_page.title[-1]) + "-2")
            )

    def test_bulk_add_for_leaf_page(self):
        root_page = SimplePage(title="Root page", slug="root-page", content="Test content")
        self.root_page.add_child(instance=root_page)
        root_page = Page.objects.get(title="Root page")

        # Add child pages to a leaf page
        manager = BulkPageManager(root_page)
        manager.bulk_add_children(self.child_pages)

        # Check if the pages were added
        self.assertEqual(root_page.get_children().count(), 200)

    def test_slug_conflict_with_existing_slug(self):
        # Add a child page with a slug that already exists
        self.root_page.add_child(
            instance=SimplePage(title="Page 1", slug="page-1", content="Test content")
        )

        # Check if error message is raised
        self.assertRaises(
            ValidationError, self.manager.bulk_add_children, self.child_pages
        )

    def test_slug_conflict_with_another_slug_of_a_page_about_to_be_added(self):
        # Add a child page with a slug that is about to be added
        self.child_pages.append(SimplePage(title="Page 1", slug="page-1"))

        # Check if error message is raised
        self.assertRaises(
            ValidationError, self.manager.bulk_add_children, self.child_pages
        )
