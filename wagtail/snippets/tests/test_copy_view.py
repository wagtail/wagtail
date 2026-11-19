from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from wagtail.test.snippets.models import StandardSnippet
from wagtail.test.testapp.models import RevisableCluster, RevisableClusterChild
from wagtail.test.utils import WagtailTestUtils


class TestSnippetCopyView(WagtailTestUtils, TestCase):
    def setUp(self):
        self.snippet = StandardSnippet.objects.create(text="Test snippet")
        self.url = reverse(
            StandardSnippet.snippet_viewset.get_url_name("copy"),
            args=(self.snippet.pk,),
        )
        self.user = self.login()

    def set_user_permissions(self, permission_codenames):
        self.user.is_superuser = False
        self.user.save()
        admin_permission = Permission.objects.get(
            content_type__app_label="wagtailadmin", codename="access_admin"
        )
        self.user.user_permissions.add(admin_permission)
        for codename in permission_codenames:
            permission = Permission.objects.get(
                content_type__app_label="snippetstests", codename=codename
            )
            self.user.user_permissions.add(permission)

    def test_without_permission(self):
        self.set_user_permissions([])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_with_only_add_permission(self):
        """
        A user must have add permission, and either edit or view permission on the source object,
        to access the copy view.
        """
        self.set_user_permissions(["add_standardsnippet"])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_with_add_and_change_permission(self):
        self.set_user_permissions(["add_standardsnippet", "change_standardsnippet"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

    def test_with_add_and_view_permission(self):
        self.set_user_permissions(["add_standardsnippet", "view_standardsnippet"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

    def test_without_add_permission(self):
        self.set_user_permissions(["change_standardsnippet", "view_standardsnippet"])

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("wagtailadmin_home"))

    def test_form_is_prefilled(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "wagtailsnippets/snippets/create.html")

        # Ensure form is prefilled
        soup = self.get_soup(response.content)
        text_input = soup.select_one('input[name="text"]')
        self.assertEqual(text_input.attrs.get("value"), "Test snippet")


class TestSnippetCopyViewAutosave(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.snippet = RevisableCluster.objects.create(text="Original")
        self.original_child = RevisableClusterChild.objects.create(
            parent=self.snippet, text="Child"
        )

    def test_autosave_after_copy_does_not_duplicate_inline_children(self):
        """
        The copy form is pre-filled with the original's child IDs. After the first
        autosave, the field updates must replace them with the IDs of the new copy's
        children, otherwise later autosaves would insert additional children.
        """
        copy_url = reverse(
            RevisableCluster.snippet_viewset.get_url_name("copy"),
            args=(self.snippet.pk,),
        )
        response = self.client.get(copy_url)
        self.assertEqual(response.status_code, 200)
        soup = self.get_soup(response.content)
        self.assertEqual(
            soup.select_one('input[name="children-0-id"]').attrs.get("value"),
            str(self.original_child.pk),
        )

        data = {
            "text": "Copy",
            "children-TOTAL_FORMS": "1",
            "children-INITIAL_FORMS": "1",
            "children-MIN_NUM_FORMS": "0",
            "children-MAX_NUM_FORMS": "1000",
            "children-0-id": str(self.original_child.pk),
            "children-0-text": "Child",
            "children-0-ORDER": "1",
            "children-0-DELETE": "",
        }
        add_url = reverse(RevisableCluster.snippet_viewset.get_url_name("add"))
        response = self.client.post(
            add_url, data, headers={"Accept": "application/json"}
        )
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        copy = RevisableCluster.objects.get(pk=response_json["pk"])
        self.assertNotEqual(copy.pk, self.snippet.pk)
        self.assertEqual(copy.children.count(), 1)

        # Apply the field updates the way the browser would, then autosave twice
        data.update(response_json["field_updates"])
        self.assertEqual(data["children-0-id"], str(copy.children.get().pk))

        edit_url = reverse(
            RevisableCluster.snippet_viewset.get_url_name("edit"), args=(copy.pk,)
        )
        for _ in range(2):
            response = self.client.post(
                edit_url, data, headers={"Accept": "application/json"}
            )
            self.assertEqual(response.status_code, 200)
            data.update(response.json()["field_updates"])

        self.assertEqual(copy.children.count(), 1)
        self.assertEqual(self.snippet.children.count(), 1)
