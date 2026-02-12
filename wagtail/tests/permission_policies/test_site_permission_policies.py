from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from wagtail.models import Site
from wagtail.permission_policies.sites import SitePermissionPolicy
from wagtail.test.testapp.models import ImportantPagesSiteSetting, TestSiteSetting
from wagtail.test.utils import WagtailTestUtils
from wagtail.tests.permission_policies.test_permission_policies import (
    PermissionPolicyTestUtils,
)


class PermissionPolicyTestCase(PermissionPolicyTestUtils, WagtailTestUtils, TestCase):
    def setUp(self):
        super().setUp()
        self.policy = SitePermissionPolicy(TestSiteSetting)

        self.default_site = Site.objects.get(is_default_site=True)
        self.other_site = Site.objects.create(
            hostname="other.example.com",
            port=80,
            root_page=self.default_site.root_page,
            is_default_site=False,
        )

        self.content_type = ContentType.objects.get_for_model(TestSiteSetting)
        self.change_permission = Permission.objects.get(
            content_type=self.content_type, codename="change_testsitesetting"
        )

        # groups
        self.site_owners = Group.objects.create(name="Site owners")
        self.site_owners.permissions.add(self.change_permission)

        self.default_site_owners = Group.objects.create(name="Default site owners")
        self.default_site_owners.site_permissions.create(
            permission=self.change_permission, site=self.default_site
        )
        self.other_site_owners = Group.objects.create(name="Other site owners")
        self.other_site_owners.site_permissions.create(
            permission=self.change_permission, site=self.other_site
        )

        self.superuser = self.create_superuser(
            "superuser", "superuser@example.com", "password"
        )
        self.inactive_superuser = self.create_superuser(
            "inactivesuperuser", "inactivesuperuser@example.com", "password"
        )
        self.inactive_superuser.is_active = False
        self.inactive_superuser.save()

        # users
        self.site_owner = self.create_user(
            "siteowner", "siteowner@example.com", "password"
        )
        self.site_owner.groups.add(self.site_owners)

        self.direct_site_owner = self.create_user(
            "directsiteowner", "directsiteowner@example.com", "password"
        )
        self.direct_site_owner.user_permissions.add(self.change_permission)

        self.default_site_owner = self.create_user(
            "defaultsiteowner", "defaultsiteowner@example.com", "password"
        )
        self.default_site_owner.groups.add(self.default_site_owners)

        self.other_site_owner = self.create_user(
            "othersiteowner", "othersiteowner@example.com", "password"
        )
        self.other_site_owner.groups.add(self.other_site_owners)


class TestSiteSettingPermissionPolicy(PermissionPolicyTestCase):
    def test_user_has_permission(self):
        self.assertUserPermissionMatrix(
            [
                (self.superuser, True),
                (self.inactive_superuser, False),
                (self.site_owner, True),
                (self.direct_site_owner, True),
                (self.default_site_owner, True),
                (self.other_site_owner, True),
            ],
            actions=["change"],
        )

    def test_user_has_permission_for_site(self):
        self.assertUserInstancePermissionMatrix(
            self.default_site,
            [
                (self.superuser, True),
                (self.inactive_superuser, False),
                (self.site_owner, True),
                (self.direct_site_owner, True),
                (self.default_site_owner, True),
                (self.other_site_owner, False),
            ],
            actions=["change"],
        )

    def test_user_has_permission_for_site_setting(self):
        site_setting = TestSiteSetting.objects.create(
            site=self.default_site,
            title="Default site",
            email="defaultsite@example.com",
        )
        self.assertUserInstancePermissionMatrix(
            site_setting,
            [
                (self.superuser, True),
                (self.inactive_superuser, False),
                (self.site_owner, True),
                (self.direct_site_owner, True),
                (self.default_site_owner, True),
                (self.other_site_owner, False),
            ],
            actions=["change"],
        )

    def test_users_with_permission(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission("change"),
            [
                self.superuser,
                self.site_owner,
                self.direct_site_owner,
                self.default_site_owner,
                self.other_site_owner,
            ],
        )

    def test_users_with_permission_for_site(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.default_site),
            [
                self.superuser,
                self.site_owner,
                self.direct_site_owner,
                self.default_site_owner,
            ],
        )

    def test_users_with_permission_for_setting(self):
        site_setting = TestSiteSetting.objects.create(
            site=self.default_site,
            title="Default site",
            email="defaultsite@example.com",
        )
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", site_setting),
            [
                self.superuser,
                self.site_owner,
                self.direct_site_owner,
                self.default_site_owner,
            ],
        )

    def test_sites_user_has_permission_for(self):
        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(self.superuser, "change"),
            [self.default_site, self.other_site],
        )

        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(
                self.inactive_superuser, "change"
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(self.site_owner, "change"),
            [self.default_site, self.other_site],
        )

        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(self.direct_site_owner, "change"),
            [self.default_site, self.other_site],
        )

        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(
                self.default_site_owner, "change"
            ),
            [self.default_site],
        )

        self.assertResultSetEqual(
            self.policy.sites_user_has_permission_for(self.other_site_owner, "change"),
            [self.other_site],
        )

    def test_instances_user_has_permission_for(self):
        site_setting = TestSiteSetting.objects.create(
            site=self.default_site,
            title="Default site",
            email="defaultsite@example.com",
        )
        # other_site does not have a TestSiteSetting instance, so will be omitted from results

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(self.superuser, "change"),
            [site_setting],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.inactive_superuser, "change"
            ),
            [],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(self.site_owner, "change"),
            [site_setting],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.direct_site_owner, "change"
            ),
            [site_setting],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.default_site_owner, "change"
            ),
            [site_setting],
        )

        self.assertResultSetEqual(
            self.policy.instances_user_has_permission_for(
                self.other_site_owner, "change"
            ),
            [],
        )


class TestOtherModelPolicy(PermissionPolicyTestCase):
    """Permissions assigned on TestSiteSetting should not 'leak' to other models."""

    def setUp(self):
        super().setUp()
        self.policy = SitePermissionPolicy(ImportantPagesSiteSetting)

    def test_user_has_permission(self):
        self.assertUserPermissionMatrix(
            [
                (self.superuser, True),
                (self.inactive_superuser, False),
                (self.site_owner, False),
                (self.direct_site_owner, False),
                (self.default_site_owner, False),
                (self.other_site_owner, False),
            ],
            actions=["change"],
        )

    def test_user_has_permission_for_site(self):
        self.assertUserInstancePermissionMatrix(
            self.default_site,
            [
                (self.superuser, True),
                (self.inactive_superuser, False),
                (self.site_owner, False),
                (self.direct_site_owner, False),
                (self.default_site_owner, False),
                (self.other_site_owner, False),
            ],
            actions=["change"],
        )

    def test_users_with_permission_for_site(self):
        self.assertResultSetEqual(
            self.policy.users_with_permission_for_instance("change", self.default_site),
            [
                self.superuser,
            ],
        )
