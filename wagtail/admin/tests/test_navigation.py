# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.test import TestCase

from wagtail.admin.navigation import (
    get_explorable_root_page, get_pages_with_direct_explore_permission)
from wagtail.tests.utils import WagtailTestUtils


class TestExplorablePages(TestCase, WagtailTestUtils):
    """
    Test the way that the explorer nav menu behaves for users with different permissions.

    This is isolated in its own test case because it requires a custom page tree and custom set of
    users and groups.
    The fixture sets up this page tree:
    ========================================================
    ID Site          Path
    ========================================================
    1              /
    2  testserver  /home/
    3  testserver  /home/about-us/
    4  example.com /home/
    5  example.com /home/content/
    6  example.com /home/content/page-1/
    7  example.com /home/content/page-2/
    9  example.com /home/content/page-2/child-1
    8  example.com /home/other-content/
    10 example.com /home-2/
    ========================================================
    Group 1 has explore and choose permissions rooted at testserver's homepage.
    Group 2 has explore and choose permissions rooted at example.com's page-1.
    Group 3 has explore and choose permissions rooted at example.com's other-content.
    User "jane" is in Group 1.
    User "bob" is in Group 2.
    User "sam" is in Groups 1 and 2.
    User "josh" is in Groups 2 and 3.
    User "mary" is is no Groups, but she has the "access wagtail admin" permission.
    User "superman" is an admin.

    Note that the Explorer Nav does not display leaf nodes.
    """

    fixtures = ['test_explorable_pages.json']

    def test_admins_see_all_pages(self):
        User = get_user_model()
        user = User.objects.get(email='superman@example.com')
        self.assertEqual(get_explorable_root_page(user).id, 1)

    def test_nav_root_for_nonadmin_is_closest_common_ancestor(self):
        User = get_user_model()
        user = User.objects.get(email='jane@example.com')
        self.assertEqual(get_explorable_root_page(user).id, 2)

    def test_nonadmin_sees_leaf_page_at_root_level(self):
        User = get_user_model()
        user = User.objects.get(email='bob@example.com')
        self.assertEqual(get_explorable_root_page(user).id, 6)

    def test_nonadmin_sees_pages_below_closest_common_ancestor(self):
        User = get_user_model()
        user = User.objects.get(email='josh@example.com')
        # Josh has permissions for /example-home/content/page-1 and /example-home/other-content,
        # of which the closest common ancestor is /example-home.
        self.assertEqual(get_explorable_root_page(user).id, 4)
        for page in get_pages_with_direct_explore_permission(user):
            self.assertIn(page.id, [6, 8])

    def test_nonadmin_sees_only_explorable_pages(self):
        # Sam has permissions for /home and /example-home/content/page-1 , of which the closest
        # common ancestor is root; we don't show root in the menu, so the top level will consist
        # of 'home' and 'example-home' (but not the sibling 'home-2', which Sam doesn't have
        # permission on)
        User = get_user_model()
        user = User.objects.get(email='sam@example.com')
        self.assertEqual(get_explorable_root_page(user).id, 1)
        for page in get_pages_with_direct_explore_permission(user):
            self.assertIn(page.id, [2, 6])

    def test_nonadmin_with_no_page_perms_cannot_explore(self):
        User = get_user_model()
        user = User.objects.get(email='mary@example.com')
        self.assertEqual(get_explorable_root_page(user), None)
