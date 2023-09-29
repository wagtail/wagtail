import json

from django.contrib.auth.models import AnonymousUser, Permission
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from wagtail import hooks
from wagtail.admin.userbar import AccessibilityItem
from wagtail.coreutils import get_dummy_request
from wagtail.models import PAGE_TEMPLATE_VAR, Page, Site
from wagtail.test.testapp.models import BusinessChild, BusinessIndex, SimplePage
from wagtail.test.utils import WagtailTestUtils
from wagtail.utils.deprecation import RemovedInWagtail60Warning


class TestUserbarTag(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.create_superuser(
            username="test", email="test@email.com", password="password"
        )
        self.homepage = Page.objects.get(id=2)

    def dummy_request(
        self,
        user=None,
        *,
        is_preview=False,
        in_preview_panel=False,
        revision_id=None,
        is_editing=False,
    ):
        request = get_dummy_request()
        request.user = user or AnonymousUser()
        request.is_preview = is_preview
        request.is_editing = is_editing
        request.in_preview_panel = in_preview_panel
        if revision_id:
            request.revision_id = revision_id
        return request

    def test_userbar_tag(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        context = Context(
            {
                PAGE_TEMPLATE_VAR: self.homepage,
                "request": self.dummy_request(self.user),
            }
        )
        with self.assertNumQueries(5):
            content = template.render(context)

        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_tag_revision(self):
        self.homepage.save_revision(user=self.user, submitted_for_moderation=True)
        revision = self.homepage.get_latest_revision()
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        context = Context(
            {
                PAGE_TEMPLATE_VAR: self.homepage,
                "request": self.dummy_request(self.user, revision_id=revision.id),
            }
        )
        with self.assertNumQueries(7), self.assertWarnsRegex(
            RemovedInWagtail60Warning,
            "ModerationEditPageItem is deprecated\. "
            "If you explicitly use this in your code, "
            "remove it from your construct_wagtail_userbar hook\.",
        ):
            content = template.render(context)

        self.assertIn("<!-- Wagtail user bar embed code -->", content)
        self.assertIn("Approve", content)

    def test_userbar_does_not_break_without_request(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}boom")
        content = template.render(Context({}))

        self.assertEqual("boom", content)

    def test_userbar_tag_self(self):
        """
        Ensure the userbar renders with `self` instead of `PAGE_TEMPLATE_VAR`
        """
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    "self": self.homepage,
                    "request": self.dummy_request(self.user),
                }
            )
        )

        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_userbar_tag_anonymous_user(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(),
                }
            )
        )

        # Make sure nothing was rendered
        self.assertEqual(content, "")

    def test_userbar_tag_no_page(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    "request": self.dummy_request(self.user),
                }
            )
        )

        self.assertIn("<!-- Wagtail user bar embed code -->", content)

    def test_edit_link(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(self.user, is_preview=False),
                }
            )
        )
        self.assertIn("<!-- Wagtail user bar embed code -->", content)
        self.assertIn("Edit this page", content)

    def test_userbar_edit_menu_in_previews(self):
        # The edit link should be visible on draft, revision, and workflow previews.
        # https://github.com/wagtail/wagtail/issues/10002
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(self.user, is_preview=True),
                }
            )
        )
        self.assertIn("<!-- Wagtail user bar embed code -->", content)
        self.assertIn("Edit this page", content)
        self.assertIn(
            reverse("wagtailadmin_pages:edit", args=(self.homepage.id,)), content
        )

    def test_userbar_edit_menu_not_in_preview(self):
        # The edit link should not be visible on PreviewOnEdit/Create views.
        # https://github.com/wagtail/wagtail/issues/8765
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(
                        self.user, is_preview=True, is_editing=True
                    ),
                }
            )
        )
        self.assertIn("<!-- Wagtail user bar embed code -->", content)
        self.assertNotIn("Edit this page", content)
        self.assertNotIn(
            reverse("wagtailadmin_pages:edit", args=(self.homepage.id,)), content
        )

    def test_userbar_not_in_preview_panel(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(
            Context(
                {
                    PAGE_TEMPLATE_VAR: self.homepage,
                    "request": self.dummy_request(
                        self.user, is_preview=True, in_preview_panel=True
                    ),
                }
            )
        )

        # Make sure nothing was rendered
        self.assertEqual(content, "")


class TestAccessibilityCheckerConfig(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.request = get_dummy_request()
        self.request.user = self.user

    def get_script(self):
        template = Template("{% load wagtailuserbar %}{% wagtailuserbar %}")
        content = template.render(Context({"request": self.request}))
        soup = self.get_soup(content)

        # Should include the configuration as a JSON script with the specific id
        return soup.find("script", id="accessibility-axe-configuration")

    def get_config(self):
        return json.loads(self.get_script().string)

    def get_hook(self, item_class):
        def customise_accessibility_checker(request, items):
            items[:] = [
                item_class() if isinstance(item, AccessibilityItem) else item
                for item in items
            ]

        return customise_accessibility_checker

    def test_config_json(self):
        script = self.get_script()
        # The configuration should be a valid non-empty JSON script
        self.assertIsNotNone(script)
        self.assertEqual(script.attrs["type"], "application/json")
        config_string = script.string.strip()
        self.assertGreater(len(config_string), 0)
        config = json.loads(config_string)
        self.assertIsInstance(config, dict)
        self.assertGreater(len(config.keys()), 0)

    def test_messages(self):
        # Should include Wagtail's error messages
        config = self.get_config()
        self.assertIsInstance(config.get("messages"), dict)
        self.assertEqual(
            config["messages"]["empty-heading"],
            "Empty heading found. Use meaningful text for screen reader users.",
        )

    def test_custom_message(self):
        class CustomMessageAccessibilityItem(AccessibilityItem):
            # Override via class attribute
            axe_messages = {
                "empty-heading": "Headings should not be empty!",
            }

            # Override via method
            def get_axe_messages(self, request):
                return {
                    **super().get_axe_messages(request),
                    "color-contrast-enhanced": "Increase colour contrast!",
                }

        with hooks.register_temporarily(
            "construct_wagtail_userbar",
            self.get_hook(CustomMessageAccessibilityItem),
        ):
            config = self.get_config()
            self.assertEqual(
                config["messages"],
                {
                    "empty-heading": "Headings should not be empty!",
                    "color-contrast-enhanced": "Increase colour contrast!",
                },
            )

    def test_unset_run_only(self):
        class UnsetRunOnlyAccessibilityItem(AccessibilityItem):
            # Example config that unsets the runOnly property so that all
            # non-experimental rules are run, but the experimental
            # focus-order-semantics rule is explicitly enabled
            axe_run_only = None
            axe_rules = {"focus-order-semantics": {"enabled": True}}

        with hooks.register_temporarily(
            "construct_wagtail_userbar",
            self.get_hook(UnsetRunOnlyAccessibilityItem),
        ):
            config = self.get_config()
            self.assertEqual(
                config["options"],
                # Should not include the runOnly property, but should include
                # the focus-order-semantics rule
                {"rules": {"focus-order-semantics": {"enabled": True}}},
            )

    def test_custom_context(self):
        class CustomContextAccessibilityItem(AccessibilityItem):
            axe_include = ["article", "section"]
            axe_exclude = [".sr-only"]

            def get_axe_exclude(self, request):
                return [*super().get_axe_exclude(request), "[data-please-ignore]"]

        with hooks.register_temporarily(
            "construct_wagtail_userbar",
            self.get_hook(CustomContextAccessibilityItem),
        ):
            config = self.get_config()
            self.assertEqual(
                config["context"],
                {
                    # Override via class attribute
                    "include": ["article", "section"],
                    "exclude": [
                        # Override via class attribute
                        ".sr-only",
                        # Should include the default exclude selectors
                        {"fromShadowDOM": ["wagtail-userbar"]},
                        # Override via method
                        "[data-please-ignore]",
                    ],
                },
            )

    def test_custom_run_only_and_rules_per_request(self):
        class CustomRunOnlyAccessibilityItem(AccessibilityItem):
            # Enable all rules within these tags
            axe_run_only = [
                "wcag2a",
                "wcag2aa",
                "wcag2aaa",
                "wcag21a",
                "wcag21aa",
                "wcag22aa",
                "best-practice",
            ]
            # Turn off the color-contrast-enhanced rule
            axe_rules = {
                "color-contrast-enhanced": {"enabled": False},
            }

            def get_axe_rules(self, request):
                # Do not turn off any rules for superusers
                if request.user.is_superuser:
                    return {}
                return super().get_axe_rules(request)

        with hooks.register_temporarily(
            "construct_wagtail_userbar",
            self.get_hook(CustomRunOnlyAccessibilityItem),
        ):
            config = self.get_config()
            self.assertEqual(
                config["options"],
                {
                    "runOnly": CustomRunOnlyAccessibilityItem.axe_run_only,
                    "rules": {},
                },
            )

            self.user.is_superuser = False
            self.user.user_permissions.add(
                Permission.objects.get(
                    content_type__app_label="wagtailadmin", codename="access_admin"
                )
            )
            self.user.save()

            config = self.get_config()
            self.assertEqual(
                config["options"],
                {
                    "runOnly": CustomRunOnlyAccessibilityItem.axe_run_only,
                    "rules": CustomRunOnlyAccessibilityItem.axe_rules,
                },
            )


class TestUserbarInPageServe(WagtailTestUtils, TestCase):
    def setUp(self):
        self.user = self.login()
        self.request = get_dummy_request(site=Site.objects.first())
        self.request.user = self.user
        self.homepage = Page.objects.get(id=2).specific
        # Use a specific page model to use our template that has {% wagtailuserbar %}
        self.page = SimplePage(title="Rendang", content="Enak", live=True)
        self.homepage.add_child(instance=self.page)

    def test_userbar_rendered(self):
        response = self.page.serve(self.request)
        response.render()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<template id="wagtail-userbar-template">')

    def test_userbar_anonymous_user_cannot_see(self):
        self.request.user = AnonymousUser()
        response = self.page.serve(self.request)
        response.render()

        # Check that the userbar is not rendered
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<template id="wagtail-userbar-template">')


class TestUserbarAddLink(WagtailTestUtils, TestCase):
    fixtures = ["test.json"]

    def setUp(self):
        self.user = self.login()
        self.request = get_dummy_request(site=Site.objects.first())
        self.request.user = self.user
        self.homepage = Page.objects.get(url_path="/home/")
        self.event_index = Page.objects.get(url_path="/home/events/").specific

        self.business_index = BusinessIndex(title="Business", live=True)
        self.homepage.add_child(instance=self.business_index)

        self.business_child = BusinessChild(title="Business Child", live=True)
        self.business_index.add_child(instance=self.business_child)

    def test_page_allowing_subpages(self):
        response = self.event_index.serve(self.request)
        response.render()
        self.assertEqual(response.status_code, 200)

        # page allows subpages, so the 'add page' button should show
        expected_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.event_index.id,)
        )
        needle = f"""
            <a href="{expected_url}" target="_parent" role="menuitem">
                <svg class="icon icon-plus w-action-icon" aria-hidden="true">
                    <use href="#icon-plus"></use>
                </svg>
                Add a child page
            </a>
            """
        self.assertTagInHTML(needle, response.content.decode())

    def test_page_disallowing_subpages(self):
        response = self.business_child.serve(self.request)
        response.render()
        self.assertEqual(response.status_code, 200)

        # page disallows subpages, so the 'add page' button shouldn't show
        expected_url = reverse(
            "wagtailadmin_pages:add_subpage", args=(self.business_index.id,)
        )
        soup = self.get_soup(response.content)
        link = soup.find("a", attrs={"href": expected_url})
        self.assertIsNone(link)


class TestUserbarModeration(WagtailTestUtils, TestCase):
    # RemovedInWagtail60Warning
    # Remove this test class when the deprecation period for the legacy
    # moderation system ends.
    # The userbar is yet to support workflows:
    # https://github.com/wagtail/wagtail/issues/9106

    def setUp(self):
        self.user = self.login()
        self.request = get_dummy_request(site=Site.objects.first())
        self.request.user = self.user
        self.homepage = Page.objects.get(id=2)
        # Use a specific page model to use our template that has {% wagtailuserbar %}
        self.page = SimplePage(title="Martabak", content="Lezat", live=True)
        self.homepage.add_child(instance=self.page)
        self.page.save_revision(submitted_for_moderation=True)
        self.revision = self.page.get_latest_revision()
        self.request.revision_id = self.revision.id

    def test_userbar_moderation(self):
        response = self.page.serve(self.request)
        with self.assertWarnsRegex(
            RemovedInWagtail60Warning,
            "ModerationEditPageItem is deprecated\. "
            "If you explicitly use this in your code, "
            "remove it from your construct_wagtail_userbar hook\.",
        ):
            response.render()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<template id="wagtail-userbar-template">')

        expected_approve_html = """
            <form action="/admin/pages/moderation/{}/approve/" target="_parent" method="post">
                <input type="hidden" name="csrfmiddlewaretoken">
                <div class="w-action">
                    <input type="submit" value="Approve" class="button" />
                </div>
            </form>
        """.format(
            self.revision.id
        )
        self.assertTagInHTML(expected_approve_html, response.content.decode())

        expected_reject_html = """
            <form action="/admin/pages/moderation/{}/reject/" target="_parent" method="post">
                <input type="hidden" name="csrfmiddlewaretoken">
                <div class="w-action">
                    <input type="submit" value="Reject" class="button" />
                </div>
            </form>
        """.format(
            self.revision.id
        )
        self.assertTagInHTML(expected_reject_html, response.content.decode())

    def test_userbar_moderation_anonymous_user_cannot_see(self):
        self.request.user = AnonymousUser()

        response = self.page.serve(self.request)
        response.render()

        # Check that the user received a forbidden message
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<template id="wagtail-userbar-template">')
