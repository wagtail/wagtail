from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse

from wagtail.documents.models import Document
from wagtail.models import Collection, CollectionViewRestriction
from wagtail.test.utils import WagtailTestUtils

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote


class TestCollectionPrivacyDocument(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.fake_file = ContentFile(b"A boring example document")
        self.fake_file.name = "test.txt"
        self.collection = Collection.objects.get(id=2)
        self.password_collection = Collection.objects.get(name="Password protected")
        self.login_collection = Collection.objects.get(name="Login protected")
        self.group_collection = Collection.objects.get(name="Group protected")
        self.view_restriction = CollectionViewRestriction.objects.get(
            collection=self.password_collection
        )
        self.event_editors_group = Group.objects.get(name="Event editors")

    def get_document(self, collection):
        secret_document = Document.objects.create(
            title="Test document",
            file=self.fake_file,
            collection=collection,
        )
        url = reverse(
            "wagtaildocs_serve", args=(secret_document.id, secret_document.filename)
        )
        response = self.client.get(url)
        return response, quote(url)

    def test_anonymous_user_must_authenticate(self):
        secret_document = Document.objects.create(
            title="Test document",
            file=self.fake_file,
            collection=self.password_collection,
        )
        doc_url = reverse(
            "wagtaildocs_serve", args=(secret_document.id, secret_document.filename)
        )
        response = self.client.get(doc_url)
        self.assertEqual(
            response.templates[0].name, "wagtaildocs/password_required.html"
        )

        submit_url = reverse(
            "wagtaildocs_authenticate_with_password", args=[self.view_restriction.id]
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="{}" />'.format(
                doc_url
            ),
            html=True,
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(
            submit_url,
            {
                "password": "wrongpassword",
                "return_url": doc_url,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.templates[0].name, "wagtaildocs/password_required.html"
        )
        self.assertContains(response, '<form action="%s"' % submit_url)

        # posting the correct password should redirect back to return_url
        response = self.client.post(
            submit_url,
            {
                "password": "swordfish",
                "return_url": doc_url,
            },
        )
        self.assertRedirects(response, doc_url)

        # now requests to the documents url should pass authentication
        self.client.get(doc_url)

        self.client.logout()

        # posting an invalid return_url will redirect to default login redirect
        with self.settings(LOGIN_REDIRECT_URL="/"):
            response = self.client.post(
                submit_url,
                {
                    "password": "swordfish",
                    "return_url": "https://invaliddomain.com",
                },
            )
            self.assertRedirects(response, "/")

    @override_settings(
        WAGTAILDOCS_PASSWORD_REQUIRED_TEMPLATE="tests/custom_docs_password_required.html"
    )
    def test_anonymous_user_must_authenticate_with_custom_password_required_template(
        self
    ):
        secret_document = Document.objects.create(
            title="Test document",
            file=self.fake_file,
            collection=self.password_collection,
        )
        doc_url = reverse(
            "wagtaildocs_serve", args=(secret_document.id, secret_document.filename)
        )
        response = self.client.get(doc_url)
        self.assertNotEqual(
            response.templates[0].name, "wagtaildocs/password_required.html"
        )
        self.assertEqual(
            response.templates[0].name, "tests/custom_docs_password_required.html"
        )

    def test_group_restriction_with_anonymous_user(self):
        response, url = self.get_document(self.group_collection)
        self.assertRedirects(response, f"/_util/login/?next={url}")

    def test_group_restriction_with_unpermitted_user(self):
        self.login(username="eventmoderator", password="password")
        response, url = self.get_document(self.group_collection)
        self.assertRedirects(response, f"/_util/login/?next={url}")

    def test_group_restriction_with_permitted_user(self):
        self.login(username="eventeditor", password="password")
        response, url = self.get_document(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_group_restriction_with_superuser(self):
        self.login(username="superuser", password="password")
        response, url = self.get_document(self.group_collection)
        self.assertEqual(response.status_code, 200)

    def test_login_restriction_with_anonymous_user(self):
        response, url = self.get_document(self.login_collection)
        self.assertRedirects(response, f"/_util/login/?next={url}")

    def test_login_restriction_with_logged_in_user(self):
        self.login(username="eventmoderator", password="password")
        response, url = self.get_document(self.login_collection)
        self.assertEqual(response.status_code, 200)

    def test_set_shared_password_with_logged_in_user(self):
        self.login()
        response = self.client.get(
            reverse("wagtailadmin_collections:set_privacy", args=(self.collection.id,)),
        )

        input_el = self.get_soup(response.content).select_one("[data-field-input]")
        self.assertEqual(response.status_code, 200)

        # check that input option for password is visible
        self.assertIn("password", response.context["form"].fields)

        # check that the option for password is visible
        self.assertIsNotNone(input_el)

    @override_settings(
        WAGTAILDOCS_PRIVATE_COLLECTION_OPTIONS={"SHARED_PASSWORD": False}
    )
    def test_unset_shared_password_with_logged_in_user(self):
        self.login()
        response = self.client.get(
            reverse("wagtailadmin_collections:set_privacy", args=(self.collection.id,)),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.context["form"].fields)
        self.assertFalse(
            response.context["form"]
            .fields["restriction_type"]
            .valid_value(CollectionViewRestriction.PASSWORD)
        )
