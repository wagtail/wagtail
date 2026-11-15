from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.api.v3.tests.base import TestV3Base
from wagtail.test.testapp.models import (
    QUOTABLE_PK,
    Advert,
    AdvertWithCustomPrimaryKey,
    UUIDSnippetWithRelations,
)
from wagtail.test.utils import WagtailTestUtils


class TestV3SnippetDeleteBase(TestV3Base, WagtailTestUtils, TestCase):
    model = None

    def setUp(self):
        super().setUp()
        self.user = self.login()

    def delete(self, pk):
        return self.client.delete(
            reverse(
                "wagtailapi_v3:delete_snippet",
                kwargs={"type": self.model._meta.label, "pk": pk},
            )
        )


class TestV3SnippetDelete(TestV3SnippetDeleteBase):
    model = Advert

    def setUp(self):
        super().setUp()
        self.advert = Advert.objects.create(text="To delete")

    def test_anonymous_returns_401(self):
        self.unauthorize()
        response = self.delete(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=401,
            detail_contains="Unauthorized",
        )

    def test_superuser_can_delete(self):
        pk = self.advert.pk
        response = self.delete(pk)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Advert.objects.filter(pk=pk).exists())

    def test_delete_with_quotable_pk(self):
        advert = AdvertWithCustomPrimaryKey.objects.create(
            advert_id=QUOTABLE_PK, text="To delete"
        )
        response = self.client.delete(
            reverse(
                "wagtailapi_v3:delete_snippet",
                kwargs={
                    "type": "tests.AdvertWithCustomPrimaryKey",
                    "pk": quote(advert.pk),
                },
            )
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            AdvertWithCustomPrimaryKey.objects.filter(pk=QUOTABLE_PK).exists()
        )

    def test_user_without_delete_permission_gets_403(self):
        user = self.create_user(username="noperms", password="password")
        self.login(user)
        response = self.delete(self.advert.pk)
        self.assert_problem_response(
            response,
            status_code=403,
            detail_contains="Permission denied",
        )

    def test_user_with_delete_permission_can_delete(self):
        user = self.create_user(username="deleter", password="password")
        user.user_permissions.add(Permission.objects.get(codename="delete_advert"))
        self.login(user)
        response = self.delete(self.advert.pk)
        self.assertEqual(response.status_code, 204)

    def test_unknown_pk_returns_404(self):
        response = self.delete(999999)
        self.assert_problem_response(
            response,
            status_code=404,
            detail_contains="No Advert matches the given query.",
        )

    def test_delete_logs_action(self):
        advert = self.advert
        response = self.delete(advert.pk)
        self.assertEqual(response.status_code, 204)
        self.assert_log_actions(advert, ["wagtail.delete"])


class TestV3SnippetDeleteWithRelations(TestV3SnippetDeleteBase):
    model = UUIDSnippetWithRelations

    def test_delete_removes_child_relations(self):
        snippet = UUIDSnippetWithRelations.objects.create(text="To delete")
        section = snippet.sections.create(
            caption="Section", link_external="http://example.com"
        )
        snippet.save()
        response = self.delete(snippet.pk)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            UUIDSnippetWithRelations.objects.filter(pk=snippet.pk).exists()
        )
        self.assertFalse(snippet.sections.model.objects.filter(pk=section.pk).exists())
