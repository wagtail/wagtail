from io import StringIO

from django.contrib.auth.models import Permission
from django.core import management
from django.test import TransactionTestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.testapp.models import SimplePage, SingleEventPage
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.timestamps import local_datetime


class TestPageSearch(WagtailTestUtils, TransactionTestCase):
    fixtures = ["test_empty.json"]

    def setUp(self):
        super().setUp()
        management.call_command(
            "update_index",
            backend_name="default",
            stdout=StringIO(),
            chunk_size=50,
        )
        self.user = self.login()

    def get(self, params=None, url_name="wagtailadmin_pages:search", **extra):
        return self.client.get(reverse(url_name), params or {}, **extra)

    def test_view(self):
        response = self.get()
        self.assertTemplateUsed(response, "wagtailadmin/pages/search.html")
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.get({"q": "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/search.html")
        self.assertEqual(response.context["query_string"], "Hello")

    def test_search_searchable_fields(self):
        # Find root page
        root_page = Page.objects.get(id=2)

        # Create a page
        root_page.add_child(
            instance=SimplePage(
                title="Greetings!",
                slug="hello",
                content="good morning",
                live=True,
                has_unpublished_changes=False,
            )
        )

        # Confirm the slug is not being searched
        response = self.get({"q": "hello"})
        self.assertNotContains(response, "There is one matching page")

        # Confirm the title is being searched
        response = self.get({"q": "greetings"})
        self.assertContains(response, "There is one matching page")

    def test_ajax(self):
        response = self.get(
            {"q": "Hello"}, url_name="wagtailadmin_pages:search_results"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, "wagtailadmin/pages/search.html")
        self.assertTemplateUsed(response, "wagtailadmin/pages/search_results.html")
        self.assertEqual(response.context["query_string"], "Hello")

    def test_pagination(self):
        # page numbers in range should be accepted
        response = self.get({"q": "Hello", "p": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/search.html")
        # page numbers out of range should return 404
        response = self.get({"q": "Hello", "p": 9999})
        self.assertEqual(response.status_code, 404)

    def test_root_can_appear_in_search_results(self):
        response = self.get({"q": "root"})
        self.assertEqual(response.status_code, 200)
        # 'pages' list in the response should contain root
        results = response.context["pages"]
        self.assertTrue(any(r.slug == "root" for r in results))

    def test_search_uses_admin_display_title_from_specific_class(self):
        # SingleEventPage has a custom get_admin_display_title method; explorer should
        # show the custom title rather than the basic database one
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        root_page.add_child(instance=new_event)
        response = self.get({"q": "lunar"})
        self.assertContains(response, "Lunar event (single event)")

    def test_search_no_perms(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()
        self.assertRedirects(self.get(), "/admin/")

    def test_search_order_by_title(self):
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        root_page.add_child(instance=new_event)

        new_event_2 = SingleEventPage(
            title="A Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        root_page.add_child(instance=new_event_2)

        response = self.get({"q": "Lunar", "ordering": "title"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [new_event_2.id, new_event.id])

        response = self.get({"q": "Lunar", "ordering": "-title"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [new_event.id, new_event_2.id])

    def test_search_order_by_updated(self):
        root_page = Page.objects.get(id=2)
        new_event = SingleEventPage(
            title="Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        root_page.add_child(instance=new_event)

        new_event_2 = SingleEventPage(
            title="Lunar event 2",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2015, 1, 1),
        )
        root_page.add_child(instance=new_event_2)

        response = self.get({"q": "Lunar", "ordering": "latest_revision_created_at"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [new_event_2.id, new_event.id])

        response = self.get({"q": "Lunar", "ordering": "-latest_revision_created_at"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [new_event.id, new_event_2.id])

    def test_search_order_by_status(self):
        root_page = Page.objects.get(id=2)
        live_event = SingleEventPage(
            title="Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
            live=True,
        )
        root_page.add_child(instance=live_event)

        draft_event = SingleEventPage(
            title="Lunar event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
            live=False,
        )
        root_page.add_child(instance=draft_event)

        response = self.get({"q": "Lunar", "ordering": "live"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [draft_event.id, live_event.id])

        response = self.get({"q": "Lunar", "ordering": "-live"})
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [live_event.id, draft_event.id])

    def test_search_filter_content_type(self):
        # Correct content_type
        response = self.get({"content_type": "demosite.standardpage"})
        self.assertEqual(response.status_code, 200)

        # Incorrect content_type
        response = self.get({"content_type": "demosite.standardpage.error"})
        self.assertEqual(response.status_code, 404)
