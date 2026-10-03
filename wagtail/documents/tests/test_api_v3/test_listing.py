from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from wagtail.models import CollectionViewRestriction

from .base import TestV3DocumentsBase


class TestV3DocumentListing(TestV3DocumentsBase):
    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v3:list_documents"), params)

    def listed_ids(self, response):
        return [item["id"] for item in response.json()["items"]]

    def test_anonymous_can_list(self):
        document = self.create_document()
        response = self.get_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(self.listed_ids(response), [document.id])

    def test_meta_fields_and_absolute_urls(self):
        self.create_document()
        item = self.get_response().json()["items"][0]
        self.assertEqual(
            set(item["meta"]),
            {"type", "detail_url", "tags", "download_url"},
        )
        self.assertEqual(item["meta"]["type"], "wagtaildocs.Document")
        self.assertTrue(
            item["meta"]["detail_url"].endswith(
                reverse(
                    "wagtailapi_v3:detail_document",
                    kwargs={"document_id": item["id"]},
                )
            )
        )
        self.assertIn(f"/documents/{item['id']}/", item["meta"]["download_url"])

    def test_search_by_title(self):
        self.create_document(title="Wagtail guide")
        self.create_document(title="Django guide")
        response = self.get_response(search="Wagtail")
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["title"], "Wagtail guide")

    def test_order_by_title(self):
        self.create_document(title="Beta")
        self.create_document(title="Alpha")
        response = self.get_response(order="title")
        self.assertEqual(
            [item["title"] for item in response.json()["items"]],
            ["Alpha", "Beta"],
        )

    def test_filter_by_title(self):
        document = self.create_document(title="Only this")
        self.create_document(title="Not this")
        response = self.get_response(title="Only this")
        self.assertEqual(self.listed_ids(response), [document.id])

    def test_listing_prefetches_tags(self):
        for index in range(3):
            document = self.create_document(title=f"Document {index}")
            document.tags.add("one", "two")
        with CaptureQueriesContext(connection) as captured:
            self.get_response()
        tag_queries = [
            query["sql"]
            for query in captured.captured_queries
            if "taggit_taggeditem" in query["sql"]
        ]
        self.assertEqual(len(tag_queries), 1)

    def test_direct_login_restriction_excludes_anonymous(self):
        collection = self.create_collection("Login only")
        document = self.create_document(collection=collection)
        CollectionViewRestriction.objects.create(
            collection=collection,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.assertNotIn(document.id, self.listed_ids(self.get_response()))

    def test_direct_login_restriction_accepts_bearer_user(self):
        collection = self.create_collection("Login only")
        document = self.create_document(collection=collection)
        CollectionViewRestriction.objects.create(
            collection=collection,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.login()
        self.assertIn(document.id, self.listed_ids(self.get_response()))

    def test_direct_group_restriction_checks_bearer_user_groups(self):
        collection = self.create_collection("Group only")
        document = self.create_document(collection=collection)
        allowed_group = Group.objects.create(name="allowed document readers")
        restriction = CollectionViewRestriction.objects.create(
            collection=collection,
            restriction_type=CollectionViewRestriction.GROUPS,
        )
        restriction.groups.add(allowed_group)

        outsider = self.create_user(username="outsider", password="password")
        self.authorize(outsider)
        self.assertNotIn(document.id, self.listed_ids(self.get_response()))

        member = self.create_user(username="member", password="password")
        member.groups.add(allowed_group)
        self.authorize(member)
        self.assertIn(document.id, self.listed_ids(self.get_response()))

    def test_direct_password_restriction_accepts_passed_session(self):
        collection = self.create_collection("Password only")
        document = self.create_document(collection=collection)
        restriction = CollectionViewRestriction.objects.create(
            collection=collection,
            restriction_type=CollectionViewRestriction.PASSWORD,
            password="swordfish",
        )
        self.assertNotIn(document.id, self.listed_ids(self.get_response()))
        session = self.client.session
        session["passed_collection_view_restrictions"] = [restriction.id]
        session.save()
        self.assertIn(document.id, self.listed_ids(self.get_response()))

    def test_ancestor_restriction_hides_descendant_document(self):
        parent = self.create_collection("Restricted parent")
        child = self.create_collection("Child", parent=parent)
        document = self.create_document(collection=child)
        CollectionViewRestriction.objects.create(
            collection=parent,
            restriction_type=CollectionViewRestriction.LOGIN,
        )
        self.assertNotIn(document.id, self.listed_ids(self.get_response()))
