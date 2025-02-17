"""
Tests for the search box in the admin side menu, and the custom search hooks.
"""

from django.contrib.auth.models import Permission
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from wagtail.admin.auth import user_has_any_page_permission
from wagtail.admin.search import SearchArea
from wagtail.test.utils import WagtailTestUtils


class BaseSearchAreaTestCase(WagtailTestUtils, TestCase):
    rf = RequestFactory()

    def search_other(self, current_url="/admin/", data=None):
        request = self.rf.get(current_url, data=data)
        request.user = self.user
        template = Template("{% load wagtailadmin_tags %}{% search_other %}")
        return template.render(Context({"request": request}))


class TestSearchAreas(BaseSearchAreaTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.login()

    def test_other_searches(self):
        search_url = reverse("wagtailadmin_pages:search")
        query = "Hello"
        base_css = "search--custom-class"
        icon = '<svg class="icon icon-custom filter-options__icon" aria-hidden="true"><use href="#icon-custom"></use></svg>'
        test_string = (
            '<a href="/customsearch/?q=%s" class="%s" is-custom="true">%sMy Search</a>'
        )
        # Testing the option link exists
        response = self.client.get(search_url, {"q": query})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/search.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/search_area.html")
        self.assertTemplateUsed(response, "wagtailadmin/shared/search_other.html")
        self.assertContains(response, test_string % (query, base_css, icon), html=True)

        # Testing is_shown
        response = self.client.get(search_url, {"q": query, "hide-option": "true"})
        self.assertNotContains(
            response, test_string % (query, base_css, icon), status_code=200, html=True
        )

        # Testing is_active
        response = self.client.get(search_url, {"q": query, "active-option": "true"})
        self.assertContains(
            response,
            test_string % (query, base_css + " nolink", icon),
            status_code=200,
            html=True,
        )

    def test_search_other(self):
        rendered = self.search_other()
        self.assertIn(reverse("wagtailadmin_pages:search"), rendered)
        self.assertIn("/customsearch/", rendered)

        self.assertIn("Pages", rendered)
        self.assertIn("My Search", rendered)


class TestSearchAreaNoPagePermissions(BaseSearchAreaTestCase):
    """
    Test the admin search when the user does not have permission to manage
    pages. The search bar should show the first available search area instead.
    """

    def setUp(self):
        self.user = self.login()
        self.assertFalse(user_has_any_page_permission(self.user))

    def create_test_user(self):
        user = super().create_test_user()
        user.is_superuser = False
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        user.save()
        return user

    def test_dashboard(self):
        """
        Check that the menu search area on the dashboard is not searching
        pages, as they are not allowed.
        """
        response = self.client.get("/admin/")
        # The menu search bar should go to /customsearch/, not /admin/pages/search/
        self.assertNotContains(response, reverse("wagtailadmin_pages:search"))
        self.assertContains(
            response,
            '{"_type": "wagtail.sidebar.SearchModule", "_args": ["/customsearch/"]}',
        )

    def test_search_other(self):
        """The pages search link should be hidden, custom search should be visible."""
        rendered = self.search_other()
        self.assertNotIn(reverse("wagtailadmin_pages:search"), rendered)
        self.assertIn("/customsearch/", rendered)

        self.assertNotIn("Pages", rendered)
        self.assertIn("My Search", rendered)


class SearchAreaComparisonTestCase(SimpleTestCase):
    """Tests the comparison functions."""

    def setUp(self):
        self.search_area1 = SearchArea("Label 1", "/url1", order=100)
        self.search_area2 = SearchArea("Label 2", "/url2", order=200)
        self.search_area3 = SearchArea("Label 1", "/url3", order=300)
        self.search_area4 = SearchArea("Label 1", "/url1", order=100)

    def test_eq(self):
        # Same label and order, should be equal
        self.assertTrue(self.search_area1 == self.search_area4)

        # Different order, should not be equal
        self.assertFalse(self.search_area1 == self.search_area2)

        # Not a SearchArea, should not be equal
        self.assertFalse(self.search_area1 == "Something")

    def test_lt(self):
        # Less order, should be True
        self.assertTrue(self.search_area1 < self.search_area2)

        # Same label, but less order, should be True
        self.assertTrue(self.search_area1 < self.search_area3)

        # Greater order, should be False
        self.assertFalse(self.search_area2 < self.search_area1)

        # Not a SearchArea, should raise TypeError
        with self.assertRaises(TypeError):
            self.search_area1 < "Something"

    def test_le(self):
        # Less order, should be True
        self.assertTrue(self.search_area1 <= self.search_area2)

        # Same label, but less order, should be True
        self.assertTrue(self.search_area1 <= self.search_area3)

        # Same object, should be True
        self.assertTrue(self.search_area1 <= self.search_area1)

        # Same label and order, should be True
        self.assertTrue(self.search_area1 <= self.search_area4)

        # Greater order, should be False
        self.assertFalse(self.search_area2 <= self.search_area1)

        # Not a SearchArea, should raise TypeError
        with self.assertRaises(TypeError):
            self.search_area1 <= "Something"

    def test_gt(self):
        # Greater order, should be True
        self.assertTrue(self.search_area2 > self.search_area1)

        # Same label, but greater order, should be True
        self.assertTrue(self.search_area3 > self.search_area1)

        # Less order, should be False
        self.assertFalse(self.search_area1 > self.search_area2)

        # Not a SearchArea, should raise TypeError
        with self.assertRaises(TypeError):
            self.search_area1 > "Something"

    def test_ge(self):
        # Greater order, should be True
        self.assertTrue(self.search_area2 >= self.search_area1)

        # Same label, but greater order, should be True
        self.assertTrue(self.search_area3 >= self.search_area1)

        # Same object, should be True
        self.assertTrue(self.search_area1 >= self.search_area1)

        # Same label and order, should be True
        self.assertTrue(self.search_area1 >= self.search_area4)

        # Less order, should be False
        self.assertFalse(self.search_area1 >= self.search_area2)

        # Not a SearchArea, should raise TypeError
        with self.assertRaises(TypeError):
            self.search_area1 >= "Something"
