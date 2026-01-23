from django.contrib.admin.utils import quote
from django.test import TestCase
from django.urls import reverse

from wagtail.test.testapp.models import ModelWithStringTypePrimaryKey
from wagtail.test.utils import WagtailTestUtils


class TestGenericIndexView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, params=None):
        return self.client.get(reverse("testapp_generic_index"), params)

    def test_non_integer_primary_key(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_object_count = response.context_data["object_list"].count()
        self.assertEqual(response_object_count, 4)
        self.assertContains(response, "first modelwithstringtypeprimarykey model")
        self.assertContains(response, "second modelwithstringtypeprimarykey model")
        soup = self.get_soup(response.content)
        h1 = soup.select_one("h1")
        self.assertIsNotNone(h1)
        self.assertEqual(h1.text.strip(), "Model with string type primary keys")


class TestGenericIndexViewWithoutModel(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, params=None):
        return self.client.get(reverse("testapp_generic_index_without_model"), params)

    def test_non_integer_primary_key(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        response_object_count = response.context_data["object_list"].count()
        self.assertEqual(response_object_count, 4)


class TestGenericCreateView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, params=None):
        return self.client.get(reverse("testapp_generic_create"), params)

    def test_get_create_view(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        h2 = soup.select_one("main h2")
        self.assertIsNotNone(h2)
        self.assertEqual(h2.text.strip(), "Model with string type primary key")
        form = soup.select_one("main form")
        self.assertIsNotNone(form)
        id_input = form.select_one("input[name='custom_id']")
        self.assertIsNotNone(id_input)
        self.assertEqual(id_input.get("type"), "text")
        content_input = form.select_one("input[name='content']")
        self.assertIsNotNone(content_input)

    def test_post_create_view(self):
        post_data = {
            "custom_id": "string-pk-3",
            "content": "third modelwithstringtypeprimarykey model",
        }
        response = self.client.post(reverse("testapp_generic_create"), post_data)
        self.assertEqual(response.status_code, 302)  # Redirect to index view
        self.assertTrue(
            ModelWithStringTypePrimaryKey.objects.filter(pk="string-pk-3").exists()
        )


class TestGenericEditView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, object_pk, params=None):
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

    def test_unquote_sensitive_primary_key(self):
        object_pk = "web_407269_1"
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "unquote-sensitive modelwithstringtypeprimarykey model"
        )

    def test_using_quote_in_edit_url(self):
        for object_pk in ('string-pk-:#?;@&=+$,"[]<>%', "web_407269_1"):
            with self.subTest(object_pk=object_pk):
                response = self.get(quote(object_pk))
                edit_url = response.context_data["action_url"]
                edit_url_pk = edit_url.split("/")[-2]
                self.assertEqual(edit_url_pk, quote(object_pk))

    def test_using_quote_in_delete_url(self):
        for object_pk in ('string-pk-:#?;@&=+$,"[]<>%', "web_407269_1"):
            with self.subTest(object_pk=object_pk):
                response = self.get(quote(object_pk))
                delete_url = response.context_data["delete_url"]
                delete_url_pk = delete_url.split("/")[-2]
                self.assertEqual(delete_url_pk, quote(object_pk))


class TestGenericDeleteView(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def get(self, object_pk, params=None):
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

    def test_with_unquote_sensitive_primary_key(self):
        object_pk = "web_407269_1"
        response = self.get(quote(object_pk))
        self.assertEqual(response.status_code, 200)
