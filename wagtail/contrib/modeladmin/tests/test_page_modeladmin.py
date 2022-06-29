from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from wagtail.models import GroupPagePermission, Page
from wagtail.test.testapp.models import BusinessIndex, EventCategory, EventPage
from wagtail.test.utils import WagtailTestUtils


class TestIndexView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def get(self, **params):
        return self.client.get("/admin/tests/eventpage/", params)

    def test_simple(self):
        response = self.get()

        self.assertEqual(response.status_code, 200)

        # There are four event pages in the test data
        self.assertEqual(response.context["result_count"], 4)

        # User has add permission
        self.assertIs(response.context["user_can_create"], True)

    def test_filter(self):
        # Filter by audience
        response = self.get(audience__exact="public")

        self.assertEqual(response.status_code, 200)

        # Only three of the event page in the test data are 'public'
        self.assertEqual(response.context["result_count"], 3)

        for eventpage in response.context["object_list"]:
            self.assertEqual(eventpage.audience, "public")

    def test_search(self):
        response = self.get(q="Someone")

        self.assertEqual(response.status_code, 200)

        # There is one eventpage where the title contains 'Someone'
        self.assertEqual(response.context["result_count"], 1)

    def test_ordering(self):
        response = self.get(o="0.1")

        self.assertEqual(response.status_code, 200)

        # There should still be four results
        self.assertEqual(response.context["result_count"], 4)

    def test_using_core_page(self):
        # The core page is slightly different to other pages, so exclude it
        response = self.client.get("/admin/wagtailcore/page/")
        self.assertEqual(response.status_code, 200)

        root_page = Page.objects.get(depth=1)
        self.assertNotIn(root_page, response.context["paginator"].object_list)


class TestExcludeFromExplorer(TestCase, WagtailTestUtils):
    fixtures = ["modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def test_attribute_effects_explorer(self):
        # The two VenuePages should appear in the venuepage list
        response = self.client.get("/admin/modeladmintest/venuepage/")
        self.assertContains(response, "Santa&#x27;s Grotto")
        self.assertContains(response, "Santa&#x27;s Workshop")

        # But when viewing the children of 'Christmas' event in explorer
        response = self.client.get("/admin/pages/4/")
        self.assertNotContains(response, "Santa&#x27;s Grotto")
        self.assertNotContains(response, "Santa&#x27;s Workshop")

        # But the other test page should...
        self.assertContains(response, "Claim your free present!")


class TestCreateView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def test_redirect_to_choose_parent(self):
        # When more than one possible parent page exists, redirect to choose_parent
        response = self.client.get("/admin/tests/eventpage/create/")
        self.assertRedirects(response, "/admin/tests/eventpage/choose_parent/")

    def test_one_parent_exists(self):
        # Create a BusinessIndex page that BusinessChild can exist under
        homepage = Page.objects.get(url_path="/home/")
        business_index = BusinessIndex(title="Business Index")
        homepage.add_child(instance=business_index)

        # When one possible parent page exists, redirect straight to the page create view
        response = self.client.get("/admin/tests/businesschild/create/")

        expected_path = "/admin/pages/add/tests/businesschild/%d/" % business_index.pk
        expected_next_path = "/admin/tests/businesschild/"
        self.assertRedirects(
            response, "%s?next=%s" % (expected_path, expected_next_path)
        )


class TestInspectView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json", "modeladmintest_test.json"]

    def setUp(self):
        self.login()

    def get(self, id):
        return self.client.get("/admin/tests/eventpage/inspect/%d/" % id)

    def test_simple(self):
        response = self.get(4)
        self.assertEqual(response.status_code, 200)

    def test_title_present(self):
        """
        The page title should appear three times. Once in the header, and two times
        in the field listing (as the actual title and as the draft title)
        """
        response = self.get(4)
        self.assertContains(response, "Christmas", 3)

    def test_manytomany_output(self):
        """
        Because ManyToMany fields are output InspectView by default, the
        `categories` for the event should output as a comma separated list
        once populated.
        """
        eventpage = EventPage.objects.get(pk=4)
        free_category = EventCategory.objects.create(name="Free")
        child_friendly_category = EventCategory.objects.create(name="Child-friendly")
        eventpage.categories = (free_category, child_friendly_category)
        eventpage.save()
        response = self.get(4)
        self.assertContains(response, "<dd>Free, Child-friendly</dd>", html=True)

    def test_false_values_displayed(self):
        """
        Boolean fields with False values should display False, rather than the
        value of `get_empty_value_display()`. For this page, those should be
        `locked`, `expired` and `has_unpublished_changes`
        """
        response = self.get(4)
        self.assertContains(response, "<dd>False</dd>", count=3, html=True)

    def test_location_present(self):
        """
        The location should appear once, in the field listing
        """
        response = self.get(4)
        self.assertContains(response, "The North Pole", 1)

    def test_non_existent(self):
        response = self.get(100)
        self.assertEqual(response.status_code, 404)

    def test_short_description_is_used_as_field_label(self):
        """
        A custom field has been added to the inspect view's `inspect_view_fields` and since
        this field has a `short_description` we expect it to be used as the field's label,
        and not use the name of the function.
        """
        response = self.client.get("/admin/modeladmintest/author/inspect/1/")
        self.assertContains(response, "Birth information")
        self.assertNotContains(response, "author_birth_string")

    def test_back_to_listing(self):
        response = self.client.get("/admin/modeladmintest/author/inspect/1/")
        # check that back to listing link exists
        expected = """
            <p class="back">
                    <a href="/admin/modeladmintest/author/">
                        <svg class="icon icon-arrow-left default" aria-hidden="true">
                            <use href="#icon-arrow-left"></use>
                        </svg>
                        Back to author list
                    </a>
            </p>
        """
        self.assertContains(response, expected, html=True)


class TestEditView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get("/admin/tests/eventpage/edit/%d/" % obj_id)

    def test_simple(self):
        response = self.get(4)

        expected_path = "/admin/pages/4/edit/"
        expected_next_path = "/admin/tests/eventpage/"
        self.assertRedirects(
            response, "%s?next=%s" % (expected_path, expected_next_path)
        )

    def test_non_existent(self):
        response = self.get(100)

        self.assertEqual(response.status_code, 404)

    def test_using_core_page(self):
        # The core page is slightly different to other pages, so exclude it
        root_page = Page.objects.get(depth=1)
        response = self.client.get("/admin/wagtailcore/page/{}/".format(root_page.id))
        self.assertEqual(response.status_code, 404)


class TestDeleteView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def get(self, obj_id):
        return self.client.get("/admin/tests/eventpage/delete/%d/" % obj_id)

    def test_simple(self):
        response = self.get(4)

        expected_path = "/admin/pages/4/delete/"
        expected_next_path = "/admin/tests/eventpage/"
        self.assertRedirects(
            response, "%s?next=%s" % (expected_path, expected_next_path)
        )


class TestChooseParentView(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def test_simple(self):
        response = self.client.get("/admin/tests/eventpage/choose_parent/")

        self.assertEqual(response.status_code, 200)

    def test_no_parent_exists(self):
        response = self.client.get("/admin/tests/businesschild/choose_parent/")

        self.assertRedirects(response, "/admin/")

    def test_post(self):
        response = self.client.post(
            "/admin/tests/eventpage/choose_parent/",
            {
                "parent_page": 2,
            },
        )

        expected_path = "/admin/pages/add/tests/eventpage/2/"
        expected_next_path = "/admin/tests/eventpage/"
        self.assertRedirects(
            response, "%s?next=%s" % (expected_path, expected_next_path)
        )

    def test_back_to_listing(self):
        response = self.client.post("/admin/tests/eventpage/choose_parent/")
        # check that back to listing link exists
        expected = """
            <p class="back">
                    <a href="/admin/tests/eventpage/">
                        <svg class="icon icon-arrow-left default" aria-hidden="true">
                            <use href="#icon-arrow-left"></use>
                        </svg>
                        Back to event page list
                    </a>
            </p>
        """
        self.assertContains(response, expected, html=True)


class TestChooseParentViewForNonSuperuser(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        homepage = Page.objects.get(url_path="/home/")
        business_index = BusinessIndex(
            title="Public Business Index",
            draft_title="Public Business Index",
        )
        homepage.add_child(instance=business_index)

        another_business_index = BusinessIndex(
            title="Another Business Index",
            draft_title="Another Business Index",
        )
        homepage.add_child(instance=another_business_index)

        secret_business_index = BusinessIndex(
            title="Private Business Index",
            draft_title="Private Business Index",
        )
        homepage.add_child(instance=secret_business_index)

        business_editors = Group.objects.create(name="Business editors")
        business_editors.permissions.add(
            Permission.objects.get(codename="access_admin")
        )
        GroupPagePermission.objects.create(
            group=business_editors, page=business_index, permission_type="add"
        )
        GroupPagePermission.objects.create(
            group=business_editors, page=another_business_index, permission_type="add"
        )

        user = self.create_user(username="test2", password="password")
        user.groups.add(business_editors)
        # Login
        self.login(username="test2", password="password")

    def test_simple(self):
        response = self.client.get("/admin/tests/businesschild/choose_parent/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Business Index")
        self.assertNotContains(response, "Private Business Index")


class TestEditorAccess(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        # Create a user
        user = self.create_user(username="test2", password="password")
        user.groups.add(Group.objects.get(pk=2))
        # Login
        self.login(username="test2", password="password")

    def test_delete_permitted(self):
        response = self.client.get("/admin/tests/eventpage/delete/4/")
        self.assertRedirects(response, "/admin/")


class TestModeratorAccess(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        # Create a user
        user = self.create_user(username="test3", password="password")
        user.groups.add(Group.objects.get(pk=1))
        # Login
        self.login(username="test3", password="password")

    def test_delete_permitted(self):
        response = self.client.get("/admin/tests/eventpage/delete/4/")
        self.assertRedirects(
            response, "/admin/pages/4/delete/?next=/admin/tests/eventpage/"
        )


class TestSearch(TestCase, WagtailTestUtils):
    fixtures = ["test_specific.json"]

    def setUp(self):
        self.login()

    def test_lookup_allowed_on_parentalkey(self):
        try:
            self.client.get(
                "/admin/tests/eventpage/?related_links__link_page__id__exact=1"
            )
        except AttributeError:
            self.fail("Lookup on parentalkey raised AttributeError unexpectedly")
