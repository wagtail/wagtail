from django.test import TestCase
from django.urls import reverse

from wagtail.models import Page
from wagtail.test.testapp.models import (
    FormPageWithRedirect,
    PageChooserModel,
    SimplePage,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestPageUsage(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    # We don't show the "Home" breadcrumb item in page views
    base_breadcrumb_items = []

    def setUp(self):
        self.user = self.login()
        self.root_page = Page.objects.get(id=2)

        with self.captureOnCommitCallbacks(execute=True):
            page = SimplePage(
                title="Hello world!",
                slug="hello-world",
                content="hello",
            )
            self.root_page.add_child(instance=page)
            page.save_revision().publish()
        self.page = SimplePage.objects.get(id=page.id)

    def test_simple(self):
        usage_url = reverse("wagtailadmin_pages:usage", args=(self.page.id,))
        response = self.client.get(usage_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertContains(response, "Usage")
        self.assertContains(response, "Hello world!")

        items = [
            {
                "url": reverse("wagtailadmin_explore_root"),
                "label": "Root",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.root_page.id,)),
                "label": "Welcome to your new Wagtail site!",
            },
            {
                "url": reverse("wagtailadmin_explore", args=(self.page.id,)),
                "label": "Hello world! (simple page)",
            },
            {
                "url": "",
                "label": "Usage",
                "sublabel": "Hello world! (simple page)",
            },
        ]
        self.assertBreadcrumbsItemsRendered(items, response.content)

        # There should be exactly one edit link, rendered as a header button
        edit_url = reverse("wagtailadmin_pages:edit", args=(self.page.id,))
        soup = self.get_soup(response.content)
        edit_links = soup.select(f"a[href='{edit_url}']")
        self.assertEqual(len(edit_links), 1)
        edit_link = edit_links[0]
        classes = edit_link.attrs.get("class")
        self.assertIn("w-header-button", classes)
        self.assertIn("button", classes)

    def test_has_private_usage(self):
        with self.captureOnCommitCallbacks(execute=True):
            PageChooserModel.objects.create(page=self.page)
        usage_url = reverse("wagtailadmin_pages:usage", args=(self.page.id,))
        response = self.client.get(usage_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertContains(response, "Usage")
        self.assertContains(response, "Hello world!")

        self.assertContains(response, "(Private page chooser model)")
        self.assertContains(response, "<td>Page chooser model</td>", html=True)

    def test_has_editable_usage(self):
        with self.captureOnCommitCallbacks(execute=True):
            form_page = FormPageWithRedirect(
                title="Contact us",
                slug="contact-us",
                to_address="to@email.com",
                from_address="from@email.com",
                subject="The subject",
                thank_you_redirect_page=self.page,
            )

            form_page = self.root_page.add_child(instance=form_page)

        usage_url = reverse("wagtailadmin_pages:usage", args=(self.page.id,))
        response = self.client.get(usage_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertContains(response, "Usage")
        self.assertContains(response, "Hello world!")

        self.assertContains(response, "Contact us")
        self.assertContains(
            response,
            reverse("wagtailadmin_pages:edit", args=(form_page.id,))
            + "#:w:contentpath=thank_you_redirect_page",
        )
        self.assertContains(response, "Thank you redirect page")
        self.assertContains(response, "<td>Form page with redirect</td>", html=True)

    def test_pagination(self):
        with self.captureOnCommitCallbacks(execute=True):
            for _ in range(50):
                PageChooserModel.objects.create(page=self.page)

        usage_url = reverse("wagtailadmin_pages:usage", args=(self.page.id,))
        response = self.client.get(f"{usage_url}?p=2")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailadmin/generic/listing.html")
        self.assertContains(response, "Page 2 of 3")
        self.assertContains(response, f"{usage_url}?p=1")
        self.assertContains(response, f"{usage_url}?p=2")
        self.assertContains(response, f"{usage_url}?p=3")
