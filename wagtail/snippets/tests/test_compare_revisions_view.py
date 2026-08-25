import datetime

from django.contrib.admin.utils import quote
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import make_aware

from wagtail.test.testapp.models import (
    RevisableChildModel,
    RevisableModel,
)
from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.template_tests import AdminTemplateTestUtils


class TestCompareRevisions(AdminTemplateTestUtils, WagtailTestUtils, TestCase):
    # Actual tests for the comparison classes can be found in test_compare.py

    def setUp(self):
        self.snippet = RevisableModel.objects.create(text="Initial revision")
        self.initial_revision = self.snippet.save_revision()
        self.initial_revision.created_at = make_aware(datetime.datetime(2022, 5, 10))
        self.initial_revision.save()

        self.snippet.text = "First edit"
        self.snippet.save()
        self.edit_revision = self.snippet.save_revision()
        self.edit_revision.created_at = make_aware(datetime.datetime(2022, 5, 11))
        self.edit_revision.save()

        self.snippet.text = "Final revision"
        self.snippet.save()
        self.final_revision = self.snippet.save_revision()
        self.final_revision.created_at = make_aware(datetime.datetime(2022, 5, 12))
        self.final_revision.save()

        self.login()

    def get(self, revision_a_id, revision_b_id):
        compare_url = reverse(
            "wagtailsnippets_tests_revisablemodel:revisions_compare",
            args=(quote(self.snippet.pk), revision_a_id, revision_b_id),
        )
        return self.client.get(compare_url)

    def test_compare_revisions(self):
        response = self.get(self.initial_revision.pk, self.edit_revision.pk)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Initial revision</span><span class="addition">First edit</span>',
            html=True,
        )

        index_url = reverse("wagtailsnippets_tests_revisablemodel:list", args=[])
        edit_url = reverse(
            "wagtailsnippets_tests_revisablemodel:edit",
            args=(self.snippet.id,),
        )
        history_url = reverse(
            "wagtailsnippets_tests_revisablemodel:history",
            args=(self.snippet.id,),
        )

        self.assertBreadcrumbsItemsRendered(
            [
                # "Snippets" index link is omitted as RevisableModel has its own menu item
                {"url": index_url, "label": "Revisable models"},
                {"url": edit_url, "label": str(self.snippet)},
                {"url": history_url, "label": "History"},
                {"url": "", "label": "Compare", "sublabel": str(self.snippet)},
            ],
            response.content,
        )

        soup = self.get_soup(response.content)
        edit_button = soup.select_one(f"a.w-header-button[href='{edit_url}']")
        self.assertIsNotNone(edit_button)
        self.assertEqual(edit_button.text.strip(), "Edit")

    def test_compare_revisions_earliest(self):
        response = self.get("earliest", self.edit_revision.pk)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Initial revision</span><span class="addition">First edit</span>',
            html=True,
        )

    def test_compare_revisions_latest(self):
        response = self.get(self.edit_revision.id, "latest")
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">First edit</span><span class="addition">Final revision</span>',
            html=True,
        )

    def test_compare_revisions_live(self):
        # Mess with the live version, bypassing revisions
        self.snippet.text = "Live edited"
        self.snippet.save(update_fields=["text"])

        response = self.get(self.final_revision.id, "live")
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            '<span class="deletion">Final revision</span><span class="addition">Live edited</span>',
            html=True,
        )


class TestCompareRevisionsWithPerUserPanels(WagtailTestUtils, TestCase):
    def setUp(self):
        self.snippet = RevisableChildModel.objects.create(
            text="Foo bar", secret_text="Secret text"
        )
        self.old_revision = self.snippet.save_revision()
        self.snippet.text = "Foo baz"
        self.snippet.secret_text = "Secret unseen note"
        self.new_revision = self.snippet.save_revision()
        self.compare_url = reverse(
            "wagtailsnippets_tests_revisablechildmodel:revisions_compare",
            args=(quote(self.snippet.pk), self.old_revision.pk, self.new_revision.pk),
        )

    def test_comparison_as_superuser(self):
        self.login()
        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Foo <span class="deletion">bar</span><span class="addition">baz</span>',
            html=True,
        )
        self.assertContains(
            response,
            'Secret <span class="deletion">text</span><span class="addition">unseen note</span>',
            html=True,
        )

    def test_comparison_as_ordinary_user(self):
        user = self.create_user(username="editor", password="password")
        add_permission = Permission.objects.get(
            content_type__app_label="tests", codename="change_revisablechildmodel"
        )
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        user.user_permissions.add(add_permission, admin_permission)
        self.login(username="editor", password="password")

        response = self.client.get(self.compare_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'Foo <span class="deletion">bar</span><span class="addition">baz</span>',
            html=True,
        )
        self.assertNotContains(response, "unseen note")
