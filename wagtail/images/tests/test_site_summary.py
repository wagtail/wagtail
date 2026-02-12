from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse

from wagtail.images.tests.utils import Image
from wagtail.images.wagtail_hooks import ImagesSummaryItem
from wagtail.models import Collection, GroupCollectionPermission, Site
from wagtail.test.utils import WagtailTestUtils


class TestImagesSummary(WagtailTestUtils, TestCase):
    @classmethod
    def setUpTestData(self):
        # Permissions
        image_content_type = ContentType.objects.get_for_model(Image)
        add_image_permission = Permission.objects.get(
            content_type=image_content_type, codename="add_image"
        )
        change_image_permission = Permission.objects.get(
            content_type=image_content_type, codename="change_image"
        )
        choose_image_permission = Permission.objects.get(
            content_type=image_content_type, codename="choose_image"
        )

        # Collections
        self.root_collection = Collection.get_first_root_node()
        self.birds_collection = self.root_collection.add_child(name="Birds")

        # Groups
        image_changers_group = Group.objects.create(name="Image changers")
        GroupCollectionPermission.objects.create(
            group=image_changers_group,
            collection=self.root_collection,
            permission=change_image_permission,
        )

        bird_adders_group = Group.objects.create(name="Bird adders")
        GroupCollectionPermission.objects.create(
            group=bird_adders_group,
            collection=self.birds_collection,
            permission=add_image_permission,
        )

        bird_choosers_group = Group.objects.create(name="Bird choosers")
        GroupCollectionPermission.objects.create(
            group=bird_choosers_group,
            collection=self.birds_collection,
            permission=choose_image_permission,
        )

        # Users
        self.superuser = self.create_superuser(
            "superuser", "superuser@example.com", "password"
        )

        # a user with add_image permission on birds via the bird_adders group
        self.bird_adder = self.create_user(
            "birdadder", "birdadder@example.com", "password"
        )
        self.bird_adder.groups.add(bird_adders_group)

        # a user with choose_image permission on birds via the bird_choosers group
        self.bird_chooser = self.create_user(
            "birdchooser", "birdchooser@example.com", "password"
        )
        self.bird_chooser.groups.add(bird_choosers_group)

        # Images

        # an image in the root owned by 'birdadder'
        self.changer_image = Image.objects.create(
            title="birdadder's image",
            collection=self.root_collection,
            uploaded_by_user=self.bird_adder,
            width=1,
            height=1,
        )

        # an image in birds owned by 'birdadder'
        self.changer_bird = Image.objects.create(
            title="birdadder's bird",
            collection=self.birds_collection,
            uploaded_by_user=self.bird_adder,
            width=2,
            height=2,
        )

        # an image in birds owned by 'birdadder'
        self.adder_bird = Image.objects.create(
            title="birdadder's bird",
            collection=self.birds_collection,
            uploaded_by_user=self.bird_adder,
            width=3,
            height=3,
        )

    def setUp(self):
        self.login(self.superuser)

    def get_request(self):
        return self.client.get(reverse("wagtailadmin_home")).wsgi_request

    def assertSummaryContains(self, content):
        summary = ImagesSummaryItem(self.get_request()).render_html()
        self.assertIn(content, summary)

    def test_site_name_is_shown(self):
        self.assertEqual(Site.objects.count(), 1)
        site = Site.objects.first()
        self.assertSummaryContains(site.site_name)

    def test_user_with_permissions_is_shown_panel(self):
        self.assertTrue(ImagesSummaryItem(self.get_request()).is_shown())

    def test_user_with_no_permissions_is_not_shown_panel(self):
        self.superuser.is_superuser = False
        self.superuser.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="wagtailadmin", codename="access_admin"
            )
        )
        self.superuser.save()
        self.assertFalse(ImagesSummaryItem(self.get_request()).is_shown())

    def test_user_sees_proper_image_count(self):
        cases = (
            (self.superuser, "3 Images"),
            (self.bird_adder, "2 Images"),
            (self.bird_chooser, "2 Images"),
        )
        for user, content in cases:
            with self.subTest(user=user):
                self.login(user)
                self.assertSummaryContains(content)
