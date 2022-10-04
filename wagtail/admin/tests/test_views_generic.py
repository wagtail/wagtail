from django.contrib.admin.utils import quote
from django.test import TestCase
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils


class TestGenericIndexView(TestCase, WagtailTestUtils):

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


class TestGenericEditView(TestCase, WagtailTestUtils):

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


class TestGenericDeleteView(TestCase, WagtailTestUtils):

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
