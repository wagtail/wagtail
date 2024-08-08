from unittest import mock

from django.contrib.admin.utils import quote
from django.test import TestCase
from django.urls import reverse

from wagtail.admin.widgets.button import ListingButton
from wagtail.test.testapp.views import TestIndexView
from wagtail.test.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail70Warning


class TestGenericIndexView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, params={}):
        return self.client.get(reverse("testapp_generic_index"), params)

    def test_non_integer_primary_key(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_object_count = response.context_data["object_list"].count()
        self.assertEqual(response_object_count, 3)
        self.assertContains(response, "first modelwithstringtypeprimarykey model")
        self.assertContains(response, "second modelwithstringtypeprimarykey model")
        soup = self.get_soup(response.content)
        h1 = soup.select_one("h1")
        self.assertIsNotNone(h1)
        self.assertEqual(h1.text.strip(), "Model with string type primary keys")

    def get_list_more_buttons(self):
        def get_list_more_buttons(view):
            return [
                ListingButton(
                    "Deprecated", "http://example.com/deprecated", "test-deprecated"
                )
            ]

        with mock.patch.object(
            TestIndexView, "get_list_more_buttons", new=get_list_more_buttons
        ), self.assertWarnsMessage(
            RemovedInWagtail70Warning,
            "Using `wagtail.admin.widgets.ListingButton` in a  `ButtonWithDropdown` "
            "is deprecated. Use `wagtail.admin.widgets.Button` instead.",
        ):
            response = self.get()

        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        dropdown_buttons = soup.select("li [data-controller='w-dropdown'] a")
        self.assertEqual(len(dropdown_buttons), 1)
        self.assertEqual(dropdown_buttons[0].text.strip(), "Deprecated")
        self.assertEqual(dropdown_buttons[0]["href"], "http://example.com/deprecated")
        self.assertEqual(dropdown_buttons[0]["class"], "test-deprecated")


class TestGenericEditView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, object_pk, params={}):
        return self.client.get(
            reverse("testapp_generic_edit", args=(object_pk,)), params
        )

    def test_non_integer_primary_key(self):
        response = self.get("string-pk-2")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "second modelwithstringtypeprimarykey model")

    def test_non_url_safe_primary_key(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "non-url-safe pk modelwithstringtypeprimarykey model"
        )

    def test_using_quote_in_edit_url(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        edit_url = response.context_data["action_url"]
        edit_url_pk = edit_url.split("/")[-2]
        self.assertEqual(edit_url_pk, quote(object_pk))

    def test_using_quote_in_delete_url(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        delete_url = response.context_data["delete_url"]
        delete_url_pk = delete_url.split("/")[-2]
        self.assertEqual(delete_url_pk, quote(object_pk))


class TestGenericDeleteView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, object_pk, params={}):
        return self.client.get(
            reverse("testapp_generic_edit", args=(object_pk,)), params
        )

    def test_with_non_integer_primary_key(self):
        response = self.get("string-pk-2")
        self.assertEqual(response.status_code, 200)

    def test_with_non_url_safe_primary_key(self):
        object_pk = 'string-pk-:#?;@&=+$,"[]<>%'
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
