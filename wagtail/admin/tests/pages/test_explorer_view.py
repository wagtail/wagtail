from django.contrib.auth.models import AbstractBaseUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import paginator
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from wagtail import hooks
from wagtail.admin.staticfiles import versioned_static
from wagtail.admin.widgets import Button
from wagtail.models import GroupPagePermission, Locale, Page, Site, Workflow
from wagtail.test.testapp.models import (
    CustomPermissionPage,
    SimplePage,
    SingleEventPage,
    StandardIndex,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.timestamps import local_datetime


class TestPageExplorer(WagtailTestUtils, TestCase):
    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=2)

        # Add child page
        self.child_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.child_page)

        # more child pages to test ordering
        self.old_page = StandardIndex(
            title="Old page",
            slug="old-page",
            latest_revision_created_at=local_datetime(2010, 1, 1),
        )
        self.root_page.add_child(instance=self.old_page)

        self.new_page = SimplePage(
            title="New page",
            slug="new-page",
            content="hello",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        self.root_page.add_child(instance=self.new_page)

        # Login
        self.user = self.login()

    def assertContainsActiveFilter(self, response, text, param):
        soup = self.get_soup(response.content)
        active_filter = soup.select_one(".w-active-filters .w-pill__content")
        clear_button = soup.select_one(".w-active-filters .w-pill__remove")
        self.assertIsNotNone(active_filter)
        self.assertEqual(active_filter.get_text(separator=" ", strip=True), text)
        self.assertIsNotNone(clear_button)
        self.assertNotIn(param, clear_button.attrs.get("data-w-swap-src-value"))
        self.assertEqual(clear_button.attrs.get("data-w-swap-reflect-value"), "true")

    def test_explore(self):
        explore_url = reverse("wagtailadmin_explore", args=(self.root_page.id,))
        response = self.client.get(explore_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(self.root_page, response.context["parent_page"])

        # child pages should be most recent first
        # (with null latest_revision_created_at at the end)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.new_page.id, self.old_page.id, self.child_page.id]
        )
        expected_new_page_copy_url = (
            reverse("wagtailadmin_pages:copy", args=(self.new_page.id,))
            + "?"
            + urlencode({"next": explore_url})
        )
        self.assertContains(response, f'href="{expected_new_page_copy_url}"')

        self.assertContains(response, "1-3 of 3")

        # Should contain a link to the history view
        # one in the header dropdown button, one beside the side panel toggles,
        # one in the status side panel
        # (root_page is a site root, not the Root page, so it should be shown)
        self.assertContains(
            response,
            reverse("wagtailadmin_pages:history", args=(self.root_page.id,)),
            count=3,
        )

        bulk_actions_js = versioned_static("wagtailadmin/js/bulk-actions.js")
        self.assertContains(
            response,
            f'<script defer src="{bulk_actions_js}"></script>',
            html=True,
        )

    def test_explore_results(self):
        explore_results_url = reverse(
            "wagtailadmin_explore_results", args=(self.root_page.id,)
        )
        response = self.client.get(explore_results_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")
        self.assertEqual(self.root_page, response.context["parent_page"])

        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.new_page.id, self.old_page.id, self.child_page.id]
        )
        # the 'next' parameter should return to the explore view, NOT
        # the partial explore_results view
        explore_url = reverse("wagtailadmin_explore", args=(self.root_page.id,))
        expected_new_page_copy_url = (
            reverse("wagtailadmin_pages:copy", args=(self.new_page.id,))
            + "?"
            + urlencode({"next": explore_url})
        )
        self.assertContains(response, f'href="{expected_new_page_copy_url}"')

        self.assertContains(response, "1-3 of 3")

    def test_explore_root(self):
        response = self.client.get(reverse("wagtailadmin_explore_root"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(Page.objects.get(id=1), response.context["parent_page"])
        self.assertIn(self.root_page, response.context["pages"])
        # Should not contain a link to the history view
        self.assertNotContains(
            response,
            reverse("wagtailadmin_pages:history", args=(1,)),
        )

    def test_explore_root_shows_icon(self):
        response = self.client.get(reverse("wagtailadmin_explore_root"))
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        # Administrator (or user with add_site permission) should see the
        # sites link with its icon
        url = reverse("wagtailsites:index")
        link = soup.select_one(f'td a[href="{url}"]')
        self.assertIsNotNone(link)
        icon = link.select_one("svg use[href='#icon-site']")
        self.assertIsNotNone(icon)

    def test_ordering(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "title"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(response.context["ordering"], "title")

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.child_page.id, self.new_page.id, self.old_page.id]
        )

    def test_ordering_by_content_type(self):
        # Delete the child_page to avoid nondeterministic ordering with the
        # new_page when ordering by content type, as they are the same type
        self.child_page.delete()

        event_page = SingleEventPage(
            title="Wagtail Space 2025",
            location="virtual",
            audience="public",
            cost="free",
            date_from="2025-06-16",
        )
        self.root_page.add_child(instance=event_page)

        orderings = {
            "content_type": (
                [self.new_page.id, self.old_page.id, event_page.id],
                "-content_type",
            ),
            "-content_type": (
                [event_page.id, self.old_page.id, self.new_page.id],
                "content_type",
            ),
        }
        url = reverse("wagtailadmin_explore", args=(self.root_page.id,))
        for ordering, (pages, reverse_param) in orderings.items():
            with self.subTest(ordering=ordering):
                response = self.client.get(url, {"ordering": ordering})
                self.assertEqual(response.status_code, 200)
                self.assertTemplateUsed(
                    response, "wagtailadmin/pages/explorable_index.html"
                )
                self.assertEqual(response.context["ordering"], ordering)

                # Child pages should be ordered by content type
                page_ids = [page.id for page in response.context["pages"]]
                self.assertEqual(page_ids, pages)

                # The type column should contain a link to order by content type
                soup = self.get_soup(response.content)
                thead = soup.select_one("main table thead")
                link = thead.select_one(f"a[href='{url}?ordering={reverse_param}']")
                self.assertIsNotNone(link)

    def test_ordering_search_results_by_created_at(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"q": "page", "ordering": "latest_revision_created_at"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")

        # child pages should be ordered by updated_at, oldest first
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.old_page.id, self.new_page.id])

    def test_ordering_search_results_by_content_type(self):
        # Ordering search results by content_type is not currently supported,
        # but should not cause an error
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"q": "page", "ordering": "content_type"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")

        # The type column should not contain a link to order by content type
        soup = self.get_soup(response.content)
        headings = soup.select("main table thead th")
        type_th = None
        for heading in headings:
            if heading.text.strip() == "Type":
                type_th = heading
        self.assertIsNotNone(type_th)
        self.assertIsNone(type_th.select_one("a"))

    def test_change_default_child_page_ordering_attribute(self):
        # save old get_default_order to reset at end of test
        # overriding class methods does not reset at end of test case
        default_order = self.root_page.__class__.admin_default_ordering
        self.root_page.__class__.admin_default_ordering = "title"
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.child_page.id, self.new_page.id, self.old_page.id]
        )
        self.assertEqual("title", self.root_page.get_admin_default_ordering())
        self.assertEqual(response.context["ordering"], "title")

        # reset default order at the end of the test
        self.root_page.__class__.admin_default_ordering = default_order

    def test_change_default_child_page_ordering_method(self):
        # save old get_default_order to reset at end of test
        # overriding class methods does not reset at end of test case
        default_order_function = self.root_page.__class__.get_admin_default_ordering

        def get_default_order(obj):
            return "-title"

        # override get_default_order_method
        self.root_page.__class__.get_admin_default_ordering = get_default_order

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual("-title", self.root_page.get_admin_default_ordering())
        self.assertEqual(
            page_ids, [self.old_page.id, self.new_page.id, self.child_page.id]
        )
        self.assertEqual(response.context["ordering"], "-title")

        # reset default order function at the end of the test
        self.root_page.__class__.get_admin_default_ordering = default_order_function

    def test_reverse_ordering(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "-title"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(response.context["ordering"], "-title")

        # child pages should be ordered by title
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.old_page.id, self.new_page.id, self.child_page.id]
        )

    def test_ordering_by_last_revision_forward(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "latest_revision_created_at"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(response.context["ordering"], "latest_revision_created_at")

        # child pages should be oldest revision first
        # (with null latest_revision_created_at at the start)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.child_page.id, self.old_page.id, self.new_page.id]
        )

    def test_invalid_ordering(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "invalid_order"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(response.context["ordering"], "-latest_revision_created_at")

    def test_reordering(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "ord"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertEqual(response.context["ordering"], "ord")

        # child pages should be ordered by native tree order (i.e. by creation time)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.child_page.id, self.old_page.id, self.new_page.id]
        )

        # Pages must not be paginated
        self.assertNotIsInstance(response.context["pages"], paginator.Page)

    def test_construct_explorer_page_queryset_hook(self):
        # testapp implements a construct_explorer_page_queryset hook
        # that only returns pages with a slug starting with 'hello'
        # when the 'polite_pages_only' URL parameter is set
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"polite_pages_only": "yes_please"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.child_page.id])

    def test_construct_explorer_page_queryset_hook_with_ordering(self):
        def set_custom_ordering(parent_page, pages, request):
            return pages.order_by("-title")

        with hooks.register_temporarily(
            "construct_explorer_page_queryset", set_custom_ordering
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )

        # child pages should be ordered by according to the hook preference
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(
            page_ids, [self.old_page.id, self.new_page.id, self.child_page.id]
        )

    def test_construct_page_listing_buttons_hook_with_new_signature(self):
        def add_dummy_button(buttons, page, user, context=None):
            if not isinstance(user, AbstractBaseUser):
                raise TypeError("expected a user instance")
            item = Button(
                label="Dummy Button",
                url="/dummy-button",
                priority=10,
            )
            buttons.append(item)

        with hooks.register_temporarily(
            "construct_page_listing_buttons", add_dummy_button
        ):
            response = self.client.get(
                reverse("wagtailadmin_explore", args=(self.root_page.id,))
            )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")
        self.assertContains(response, "Dummy Button")
        self.assertContains(response, "/dummy-button")

    def make_pages(self):
        for i in range(150):
            self.root_page.add_child(
                instance=SimplePage(
                    title="Page " + str(i),
                    slug="page-" + str(i),
                    content="hello",
                )
            )

    def test_pagination(self):
        self.make_pages()

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)), {"p": 2}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")

        # Check that we got the correct page
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertContains(response, "51-100 of 153")

    def test_pagination_invalid(self):
        self.make_pages()

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"p": "Hello World!"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")

        # Check that we got page one
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_pagination_out_of_range(self):
        self.make_pages()

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)), {"p": 99999}
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")

        # Check that we got the last page
        self.assertEqual(
            response.context["page_obj"].number,
            response.context["paginator"].num_pages,
        )

    def test_no_pagination_with_custom_ordering(self):
        self.make_pages()

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"ordering": "ord"},
        )

        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index.html")

        # Check that we don't have a paginator page object
        self.assertIsNone(response.context["page_obj"])

        # Check that all pages are shown
        self.assertContains(response, "1-153 of 153")
        self.assertEqual(len(response.context["pages"]), 153)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_no_thousand_separators_in_bulk_action_checkbox(self):
        """
        Test that the USE_THOUSAND_SEPARATOR setting does mess up object IDs in
        bulk actions checkboxes
        """
        self.root_page.add_child(
            instance=SimplePage(
                pk=1000,
                title="Page 1000",
                slug="page-1000",
                content="hello",
            )
        )
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        expected = 'data-object-id="1000"'
        self.assertContains(response, expected)

    def test_listing_uses_specific_models(self):
        # SingleEventPage has custom URL routing; the 'live' link in the listing
        # should show the custom URL, which requires us to use the specific version
        # of the class
        self.new_event = SingleEventPage(
            title="New event",
            location="the moon",
            audience="public",
            cost="free",
            date_from="2001-01-01",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        self.root_page.add_child(instance=self.new_event)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "/new-event/pointless-suffix/")

    def make_event_pages(self, count):
        for i in range(count):
            self.root_page.add_child(
                instance=SingleEventPage(
                    title="New event " + str(i),
                    location="the moon",
                    audience="public",
                    cost="free",
                    date_from="2001-01-01",
                    latest_revision_created_at=local_datetime(2016, 1, 1),
                )
            )

    def test_exploring_uses_specific_page_with_custom_display_title(self):
        # SingleEventPage has a custom get_admin_display_title method; explorer should
        # show the custom title rather than the basic database one
        self.make_event_pages(count=1)
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        self.assertContains(response, "New event 0 (single event)")

        new_event = SingleEventPage.objects.latest("pk")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(new_event.id,))
        )
        self.assertContains(response, "New event 0 (single event)")

    def test_parent_page_is_specific(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.child_page.id,))
        )
        self.assertEqual(response.status_code, 200)

        self.assertIsInstance(response.context["parent_page"], SimplePage)

    def test_explorer_no_perms(self):
        self.user.is_superuser = False
        self.user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.user.save()

        admin = reverse("wagtailadmin_home")
        self.assertRedirects(
            self.client.get(reverse("wagtailadmin_explore", args=(self.root_page.id,))),
            admin,
        )
        self.assertRedirects(
            self.client.get(reverse("wagtailadmin_explore_root")), admin
        )

    def test_explore_with_missing_page_model(self):
        # Create a ContentType that doesn't correspond to a real model
        missing_page_content_type = ContentType.objects.create(
            app_label="tests", model="missingpage"
        )
        # Turn /home/old-page/ into this content type
        Page.objects.filter(id=self.old_page.id).update(
            content_type=missing_page_content_type
        )

        # try to browse the listing that contains the missing model
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")

        # try to browse into the page itself
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.old_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")

    def test_search(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"q": "old"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/explorable_index.html")

        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.old_page.id])
        self.assertContains(response, "Search the whole site")

    def test_search_results(self):
        response = self.client.get(
            reverse("wagtailadmin_explore_results", args=(self.root_page.id,)),
            {"q": "old"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/pages/index_results.html")

        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.old_page.id])
        self.assertContains(response, "1-1 of 1")

    def test_search_searches_descendants(self):
        response = self.client.get(reverse("wagtailadmin_explore_root"), {"q": "old"})
        self.assertEqual(response.status_code, 200)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.old_page.id])
        # Results that are not immediate children of the current page should show their parent
        self.assertContains(
            response,
            '<a href="/admin/pages/2/"><svg class="icon icon-arrow-right default" aria-hidden="true"><use href="#icon-arrow-right"></use></svg>Welcome to your new Wagtail site!</a>',
            html=True,
        )

        # search results should not include pages outside parent_page's descendants
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.new_page.id,)),
            {"q": "old"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [])

    def test_search_whole_tree(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.new_page.id,)),
            {"q": "old", "search_all": "1"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = [page.id for page in response.context["pages"]]
        self.assertEqual(page_ids, [self.old_page.id])
        self.assertContains(
            response,
            "Search in '<span class=\"w-title-ellipsis\">New page (simple page)</span>'",
        )

    def test_filter_by_page_type(self):
        new_page_child = SimplePage(
            title="New page child", slug="new-page-child", content="new page child"
        )
        self.new_page.add_child(instance=new_page_child)
        page_type_pk = ContentType.objects.get_for_model(SimplePage).pk
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"content_type": page_type_pk},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(
            page_ids, {self.child_page.id, self.new_page.id, new_page_child.id}
        )
        self.assertContainsActiveFilter(
            response,
            "Page type: Simple page",
            f"content_type={page_type_pk}",
        )

        # "Page" should not be listed as a content type
        soup = self.get_soup(response.content)
        page_type_labels = {
            list(label.children)[-1].strip()
            for label in soup.select("#id_content_type label")
        }
        self.assertIn("Simple page", page_type_labels)
        self.assertNotIn("Page", page_type_labels)

    @override_settings(WAGTAIL_I18N_ENABLED=True)
    def test_filter_by_locale_and_search(self):
        fr_locale = Locale.objects.create(language_code="fr")
        self.root_page.copy_for_translation(fr_locale, copy_parents=True)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"locale": "en", "q": "hello"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertIn(self.child_page.id, page_ids)
        self.assertContainsActiveFilter(
            response,
            "Locale: English",
            "locale=en",
        )

    def test_filter_by_date_updated(self):
        new_page_child = SimplePage(
            title="New page child",
            slug="new-page-child",
            content="new page child",
            latest_revision_created_at=local_datetime(2016, 1, 1),
        )
        self.new_page.add_child(instance=new_page_child)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"latest_revision_created_at_from": "2015-01-01"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(page_ids, {self.new_page.id, new_page_child.id})
        self.assertContainsActiveFilter(
            response,
            "Date updated: Jan. 1, 2015 - any",
            "latest_revision_created_at_from=2015-01-01",
        )

    def test_filter_by_owner(self):
        barry = self.create_user(
            "barry", password="password", first_name="Barry", last_name="Manilow"
        )
        self.create_user(
            "larry", password="password", first_name="Larry", last_name="King"
        )

        new_page_child = SimplePage(
            title="New page child",
            slug="new-page-child",
            content="new page child",
            owner=barry,
        )
        self.new_page.add_child(instance=new_page_child)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
        )
        self.assertEqual(response.status_code, 200)
        # Only users who own any pages should be listed in the filter
        self.assertContains(response, "Barry Manilow")
        self.assertNotContains(response, "Larry King")

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"owner": barry.pk},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(page_ids, {new_page_child.id})
        self.assertContainsActiveFilter(
            response,
            "Owner: Barry Manilow",
            f"owner={barry.pk}",
        )

    def test_filter_by_edited_by_user(self):
        barry = self.create_superuser(
            "barry", password="password", first_name="Barry", last_name="Manilow"
        )
        self.create_user(
            "larry", password="password", first_name="Larry", last_name="King"
        )

        self.login(username="barry", password="password")

        post_data = {
            "title": "Hello world!",
            "content": "hello from Barry",
            "slug": "hello-world",
        }
        response = self.client.post(
            reverse("wagtailadmin_pages:edit", args=(self.child_page.id,)), post_data
        )
        self.assertEqual(response.status_code, 302)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"edited_by": barry.pk},
        )
        self.assertEqual(response.status_code, 200)
        # Only users who have edited any pages should be listed in the filter
        self.assertContains(response, "Barry Manilow")
        self.assertNotContains(response, "Larry King")

        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(page_ids, {self.child_page.id})
        self.assertContainsActiveFilter(
            response,
            "Edited by: Barry Manilow",
            f"edited_by={barry.pk}",
        )

    def test_filter_by_site(self):
        new_site = Site.objects.create(
            hostname="new.example.com", root_page=self.new_page
        )
        new_page_child = SimplePage(
            title="New page child",
            slug="new-page-child",
            content="new page child",
        )
        self.new_page.add_child(instance=new_page_child)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"site": new_site.pk},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(page_ids, {self.new_page.id, new_page_child.id})
        self.assertContainsActiveFilter(
            response,
            "Site: new.example.com",
            f"site={new_site.pk}",
        )

    def test_filter_by_has_child_pages(self):
        new_page_child = SimplePage(
            title="New page child",
            slug="new-page-child",
            content="new page child",
        )
        self.new_page.add_child(instance=new_page_child)

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"has_child_pages": "true"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(page_ids, {self.new_page.id})
        self.assertContainsActiveFilter(
            response,
            "Has child pages: Yes",
            "has_child_pages=true",
        )

        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"has_child_pages": "false"},
        )
        self.assertEqual(response.status_code, 200)
        page_ids = {page.id for page in response.context["pages"]}
        self.assertEqual(
            page_ids, {self.child_page.id, self.old_page.id, new_page_child.id}
        )
        self.assertContainsActiveFilter(
            response,
            "Has child pages: No",
            "has_child_pages=false",
        )

    def test_invalid_filter(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.root_page.id,)),
            {"has_child_pages": "unknown"},
        )
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        active_filters = soup.select_one(".w-active-filters")
        self.assertIsNone(active_filters)
        error_message = soup.select_one(".w-field__errors .error-message")
        self.assertIsNotNone(error_message)
        self.assertEqual(
            error_message.string.strip(),
            "Select a valid choice. unknown is not one of the available choices.",
        )

    def test_explore_custom_permissions(self):
        page = CustomPermissionPage(title="Page with custom perms", slug="custom-perms")
        self.root_page.add_child(instance=page)
        response = self.client.get(reverse("wagtailadmin_explore", args=(page.id,)))
        self.assertEqual(response.status_code, 200)
        # Respecting PagePermissionTester.can_view_revisions(),
        # should not contain a link to the history view
        self.assertNotContains(
            response,
            reverse("wagtailadmin_pages:history", args=(page.id,)),
        )


class TestBreadcrumb(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_breadcrumb_next_present(self):
        self.user = self.login()

        # get the explorer view for a subpage of a SimplePage
        page = Page.objects.get(url_path="/home/secret-plans/steal-underpants/")
        response = self.client.get(reverse("wagtailadmin_explore", args=(page.id,)))
        self.assertEqual(response.status_code, 200)

        # The breadcrumbs controller identifier should be present
        self.assertContains(response, 'data-controller="w-breadcrumbs"')

    def test_breadcrumb_uses_specific_titles(self):
        self.user = self.login()

        # get the explorer view for a subpage of a SimplePage
        page = Page.objects.get(url_path="/home/secret-plans/steal-underpants/")
        response = self.client.get(reverse("wagtailadmin_explore", args=(page.id,)))

        # The breadcrumb should pick up SimplePage's overridden get_admin_display_title method
        expected_url = reverse(
            "wagtailadmin_explore",
            args=(Page.objects.get(url_path="/home/secret-plans/").id,),
        )

        expected = (
            """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="%s">
                    Secret plans (simple page)
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
            % expected_url
        )

        self.assertContains(response, expected, html=True)


class TestPageExplorerSidePanel(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def test_side_panel_present(self):
        self.user = self.login()

        # get the explorer view for a subpage of a SimplePage
        page = Page.objects.get(url_path="/home/secret-plans/steal-underpants/")
        response = self.client.get(reverse("wagtailadmin_explore", args=(page.id,)))
        self.assertEqual(response.status_code, 200)

        # The side panel should be present with data-form-side-explorer attribute
        html = response.content.decode()
        self.assertTagInHTML(
            "<aside data-form-side data-form-side-explorer>",
            html,
            allow_extra_attrs=True,
        )


class TestPageExplorerSignposting(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        # Find root page
        self.root_page = Page.objects.get(id=1)

        # Find page with an associated site
        self.site_page = Page.objects.get(id=2)

        # Add another top-level page (which will have no corresponding site record)
        self.no_site_page = SimplePage(
            title="Hello world!",
            slug="hello-world",
            content="hello",
        )
        self.root_page.add_child(instance=self.no_site_page)

    # Tests for users that have both add-site permission, and explore permission at the given view;
    # warning messages should include advice re configuring sites

    def test_admin_at_root(self):
        self.login(username="superuser", password="password")
        response = self.client.get(reverse("wagtailadmin_explore_root"))
        self.assertEqual(response.status_code, 200)
        # Administrator (or user with add_site permission) should get the full message
        # about configuring sites
        self.assertContains(
            response,
            (
                "The root level is where you can add new sites to your Wagtail installation. "
                "Pages created here will not be accessible at any URL until they are associated with a site."
            ),
        )
        self.assertContains(
            response, """<a href="/admin/sites/">Configure a site now.</a>"""
        )

    def test_searching_at_root(self):
        self.login(username="superuser", password="password")

        # Message about root level should not show when searching or filtering
        response = self.client.get(reverse("wagtailadmin_explore_root"), {"q": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "The root level is where you can add new sites to your Wagtail installation.",
        )
        response = self.client.get(
            reverse("wagtailadmin_explore_root"), {"has_child_pages": "true"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "The root level is where you can add new sites to your Wagtail installation.",
        )

    def test_admin_at_non_site_page(self):
        self.login(username="superuser", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.no_site_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        # Administrator (or user with add_site permission) should get a warning about
        # unroutable pages, and be directed to the site config area
        self.assertContains(
            response,
            (
                "There is no site set up for this location. "
                "Pages created here will not be accessible at any URL until a site is associated with this location."
            ),
        )
        self.assertContains(
            response, """<a href="/admin/sites/">Configure a site now.</a>"""
        )

    def test_searching_at_non_site_page(self):
        self.login(username="superuser", password="password")

        # Message about unroutable pages should not show when searching or filtering
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.no_site_page.id,)),
            {"q": "hello"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "There is no site set up for this location.",
        )
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.no_site_page.id,)),
            {"has_child_pages": "true"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            "There is no site set up for this location.",
        )

    def test_admin_at_site_page(self):
        self.login(username="superuser", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.site_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        # There should be no warning message here
        self.assertNotContains(response, "Pages created here will not be accessible")

    # Tests for standard users that have explore permission at the given view;
    # warning messages should omit advice re configuring sites

    def test_nonadmin_at_root(self):
        # Assign siteeditor permission over no_site_page, so that the deepest-common-ancestor
        # logic allows them to explore root
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.no_site_page,
            permission_type="add",
        )
        self.login(username="siteeditor", password="password")
        response = self.client.get(reverse("wagtailadmin_explore_root"))

        self.assertEqual(response.status_code, 200)
        # Non-admin should get a simple "create pages as children of the homepage" prompt
        self.assertContains(
            response,
            "Pages created here will not be accessible at any URL. "
            "To add pages to an existing site, create them as children of the homepage.",
        )

    def test_nonadmin_at_non_site_page(self):
        # Assign siteeditor permission over no_site_page
        GroupPagePermission.objects.create(
            group=Group.objects.get(name="Site-wide editors"),
            page=self.no_site_page,
            permission_type="add",
        )
        self.login(username="siteeditor", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.no_site_page.id,))
        )

        self.assertEqual(response.status_code, 200)
        # Non-admin should get a warning about unroutable pages
        self.assertContains(
            response,
            (
                "There is no site record for this location. "
                "Pages created here will not be accessible at any URL."
            ),
        )

    def test_nonadmin_at_site_page(self):
        self.login(username="siteeditor", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.site_page.id,))
        )
        self.assertEqual(response.status_code, 200)
        # There should be no warning message here
        self.assertNotContains(response, "Pages created here will not be accessible")

    # Tests for users that have explore permission *somewhere*, but not at the view being tested;
    # in all cases, they should be redirected to their explorable root

    def test_bad_permissions_at_root(self):
        # 'siteeditor' does not have permission to explore the root
        self.login(username="siteeditor", password="password")
        response = self.client.get(reverse("wagtailadmin_explore_root"))

        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response["Location"]),
            (302, reverse("wagtailadmin_explore", args=(self.site_page.pk,))),
        )

    def test_bad_permissions_at_non_site_page(self):
        # 'siteeditor' does not have permission to explore no_site_page
        self.login(username="siteeditor", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.no_site_page.id,))
        )

        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response["Location"]),
            (302, reverse("wagtailadmin_explore", args=(self.site_page.pk,))),
        )

    def test_bad_permissions_at_site_page(self):
        # Adjust siteeditor's permission so that they have permission over no_site_page
        # instead of site_page
        Group.objects.get(name="Site-wide editors").page_permissions.update(
            page_id=self.no_site_page.id
        )
        self.login(username="siteeditor", password="password")
        response = self.client.get(
            reverse("wagtailadmin_explore", args=(self.site_page.id,))
        )
        # Users without permission to explore here should be redirected to their explorable root.
        self.assertEqual(
            (response.status_code, response["Location"]),
            (302, reverse("wagtailadmin_explore", args=(self.no_site_page.pk,))),
        )


class TestExplorablePageVisibility(WagtailTestUtils, TestCase):
    """
    Test the way that the Explorable Pages functionality manifests within the Explorer.
    This is isolated in its own test case because it requires a custom page tree and custom set of
    users and groups.
    The fixture sets up this page tree:
    ========================================================
    ID Site          Path
    ========================================================
    1              /
    2  testserver  /home/
    3  testserver  /home/about-us/
    4  example.com /example-home/
    5  example.com /example-home/content/
    6  example.com /example-home/content/page-1/
    7  example.com /example-home/content/page-2/
    9  example.com /example-home/content/page-2/child-1
    8  example.com /example-home/other-content/
    10 example2.com /home-2/
    ========================================================
    Group 1 has explore and choose permissions rooted at testserver's homepage.
    Group 2 has explore and choose permissions rooted at example.com's page-1.
    Group 3 has explore and choose permissions rooted at example.com's other-content.
    User "jane" is in Group 1.
    User "bob" is in Group 2.
    User "sam" is in Groups 1 and 2.
    User "josh" is in Groups 2 and 3.
    User "mary" is is no Groups, but she has the "access wagtail admin" permission.
    User "superman" is an admin.
    """

    fixtures = ["test_explorable_pages.json"]

    # Integration tests adapted from @coredumperror

    def test_admin_can_explore_every_page(self):
        self.login(username="superman", password="password")
        for page in Page.objects.all():
            response = self.client.get(reverse("wagtailadmin_explore", args=[page.pk]))
            self.assertEqual(response.status_code, 200)

    def test_admin_sees_root_page_as_explorer_root(self):
        self.login(username="superman", password="password")
        response = self.client.get(reverse("wagtailadmin_explore_root"))
        self.assertEqual(response.status_code, 200)
        # Administrator should see the full list of children of the Root page.
        self.assertContains(response, "Welcome to testserver!")
        self.assertContains(response, "Welcome to example.com!")

    def test_admin_sees_breadcrumbs_up_to_root_page(self):
        self.login(username="superman", password="password")
        response = self.client.get(reverse("wagtailadmin_explore", args=[6]))
        self.assertEqual(response.status_code, 200)
        expected = """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="/admin/pages/">
                    Root
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>

        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="/admin/pages/4/">
                    Welcome to example.com!
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="/admin/pages/5/">
                    Content
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
        self.assertContains(response, expected, html=True)

    def test_nonadmin_sees_breadcrumbs_up_to_cca(self):
        self.login(username="josh", password="password")
        response = self.client.get(reverse("wagtailadmin_explore", args=[6]))
        self.assertEqual(response.status_code, 200)
        # While at "Page 1", Josh should see the breadcrumbs leading only as far back as the example.com homepage,
        # since it's his Closest Common Ancestor.
        expected = """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="/admin/pages/4/">
                    Welcome to example.com!
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
        self.assertContains(response, expected, html=True)
        expected = """
            <li class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-max-w-0" data-w-breadcrumbs-target="content" hidden>
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label" href="/admin/pages/5/">
                    Content
                </a>
                <svg class="icon icon-arrow-right w-w-4 w-h-4 w-ml-3" aria-hidden="true">
                    <use href="#icon-arrow-right"></use>
                </svg>
            </li>
        """
        self.assertContains(response, expected, html=True)

    def test_nonadmin_sees_non_hidden_root(self):
        self.login(username="josh", password="password")
        response = self.client.get(reverse("wagtailadmin_explore", args=[4]))
        self.assertEqual(response.status_code, 200)
        # When Josh is viewing his visible root page, he should the page title as a non-hidden, single-item breadcrumb.
        expected = """
            <li
                class="w-h-full w-flex w-items-center w-overflow-hidden w-transition w-duration-300 w-whitespace-nowrap w-flex-shrink-0 w-font-bold" data-w-breadcrumbs-target="content">
                <a class="w-flex w-items-center w-text-text-label w-pr-0.5 w-text-14 w-no-underline w-outline-offset-inside w-border-b w-border-b-2 w-border-transparent w-box-content hover:w-border-current hover:w-text-text-label"
                   href="/admin/pages/4/">
                    Welcome to example.com!
                </a>
            </li>
        """
        self.assertContains(response, expected, html=True)

    def test_admin_home_page_changes_with_permissions(self):
        self.login(username="bob", password="password")
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        # Bob should only see the welcome for example.com, not testserver
        self.assertContains(response, "example.com")
        self.assertNotContains(response, "testserver")

    def test_breadcrumb_with_no_user_permissions(self):
        self.login(username="mary", password="password")
        response = self.client.get(reverse("wagtailadmin_home"))
        self.assertEqual(response.status_code, 200)
        # Since Mary has no page permissions, she should not see the breadcrumb
        self.assertNotContains(
            response,
            """<li class="home breadcrumb-item"><a class="breadcrumb-link" href="/admin/pages/4/" class="icon icon-home text-replace">Home</a></li>""",
        )


@override_settings(WAGTAIL_I18N_ENABLED=True)
class TestLocaleSelector(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.events_page = Page.objects.get(url_path="/home/events/")
        self.fr_locale = Locale.objects.create(language_code="fr")
        self.translated_events_page = self.events_page.copy_for_translation(
            self.fr_locale, copy_parents=True
        )
        self.user = self.login()

    def test_locale_selector(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=[self.events_page.id])
        )
        html = response.content.decode()

        self.assertContains(response, 'id="status-sidebar-english"')
        self.assertContains(response, "Switch locales")

        add_translation_url = reverse(
            "wagtailadmin_explore", args=[self.translated_events_page.id]
        )
        self.assertTagInHTML(
            f'<a href="{add_translation_url}" lang="fr">French</a>',
            html,
            allow_extra_attrs=True,
        )

    @override_settings(WAGTAIL_I18N_ENABLED=False)
    def test_locale_selector_not_present_when_i18n_disabled(self):
        response = self.client.get(
            reverse("wagtailadmin_explore", args=[self.events_page.id])
        )
        html = response.content.decode()

        self.assertNotContains(response, "Switch locales")

        add_translation_url = reverse(
            "wagtailadmin_explore", args=[self.translated_events_page.id]
        )
        self.assertTagInHTML(
            f'<a href="{add_translation_url}" lang="fr">French</a>',
            html,
            allow_extra_attrs=True,
            count=0,
        )


class TestInWorkflowStatus(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    @classmethod
    def setUpTestData(cls):
        cls.event_index = Page.objects.get(url_path="/home/events/")
        cls.christmas = Page.objects.get(url_path="/home/events/christmas/").specific
        cls.saint_patrick = Page.objects.get(
            url_path="/home/events/saint-patrick/"
        ).specific
        cls.christmas.save_revision()
        cls.saint_patrick.save_revision()
        cls.url = reverse("wagtailadmin_explore", args=[cls.event_index.pk])

    def setUp(self):
        self.user = self.login()

    def test_in_workflow_status(self):
        workflow = Workflow.objects.first()
        workflow.start(self.christmas, self.user)
        workflow.start(self.saint_patrick, self.user)

        # Warm up cache
        self.client.get(self.url)

        with self.assertNumQueries(44):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)

        for page in [self.christmas, self.saint_patrick]:
            status = soup.select_one(f'a.w-status[href="{page.url}"]')
            self.assertIsNotNone(status)
            self.assertEqual(
                status.text.strip(), "Current page status: live + in moderation"
            )
            self.assertEqual(page.status_string, "live + in moderation")
