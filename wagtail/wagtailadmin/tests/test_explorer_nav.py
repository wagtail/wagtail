# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.core.urlresolvers import reverse
from django.test import TestCase

from wagtail.tests.utils import WagtailTestUtils
from wagtail.wagtailcore.models import Page


class TestExplorerNavView(TestCase, WagtailTestUtils):
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
    Group 2 has explore and choose permissions rooted at exammple.com's page-1.
    Group 3 has explore and choose permissions rooted at exammple.com's other-content.
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
        self.assertTrue(self.client.login(username='superman', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(len(response.context['nodes']), 3)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=2))
        self.assertEqual(response.context['nodes'][1][0], Page.objects.get(id=4))
        self.assertEqual(response.context['nodes'][1][1][0][0], Page.objects.get(id=5))
        self.assertEqual(response.context['nodes'][1][1][0][1][0][0], Page.objects.get(id=7))
        # Even though example.com's Home 2 has no children, it's still displayed because it's at
        # the top menu level for this user
        self.assertEqual(response.context['nodes'][2][0], Page.objects.get(id=10))

    def test_nav_root_for_nonadmin_is_closest_common_ancestor(self):
        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(len(response.context['nodes']), 1)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=2))
        self.client.logout()

        self.assertTrue(self.client.login(username='sam', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(len(response.context['nodes']), 2)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=2))
        self.assertEqual(response.context['nodes'][1][0], Page.objects.get(id=4))

    def test_nonadmin_sees_leaf_pages_at_root_level(self):
        self.assertTrue(self.client.login(username='bob', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        # Bob's group's CCA is a leaf node, so by the naive "don't show childless pages" rule
        # he would not be shown any nodes. This would be bad, so we make an exception whereby
        # childless pages at the user's top level are shown
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(len(response.context['nodes']), 1)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=6))
        self.assertEqual(len(response.context['nodes'][0][1]), 0)

    def test_nonadmin_sees_pages_below_closest_common_ancestor(self):
        self.assertTrue(self.client.login(username='josh', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        # Josh has permissions for /example-home/content/page-1 and /example-home/other-content ,
        # of which the closest common ancestor is /example-home . However, since he doesn't need
        # access to example-home itself, the menu begins at its children ('content' and
        # 'other-content') instead
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')

        self.assertEqual(len(response.context['nodes']), 2)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=5))
        # page-1 is childless, but user has direct permission on it, so it should be shown
        self.assertEqual(len(response.context['nodes'][0][1]), 1)
        self.assertEqual(response.context['nodes'][0][1][0][0], Page.objects.get(id=6))
        self.assertEqual(len(response.context['nodes'][0][1][0][1]), 0)

        self.assertEqual(response.context['nodes'][1][0], Page.objects.get(id=8))
        self.assertEqual(len(response.context['nodes'][1][1]), 0)

    def test_nonadmin_sees_only_explorable_pages(self):
        self.assertTrue(self.client.login(username='sam', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        # Sam has permissions for /home and /example-home/content/page-1 , of which the closest
        # common ancestor is root; we don't show root in the menu, so the top level will consist
        # of 'home' and 'example-home' (but not the sibling 'home-2', which Sam doesn't have
        # permission on)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')

        self.assertEqual(len(response.context['nodes']), 2)
        # Sam should see the testserver homepage, the example.com homepage, and the Content page,
        # but should not see Page 2.
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=2))
        self.assertEqual(response.context['nodes'][1][0], Page.objects.get(id=4))
        self.assertEqual(response.context['nodes'][1][1][0][0], Page.objects.get(id=5))
        self.assertEqual(len(response.context['nodes'][1][1][0][1]), 1)
        # page-1 is included in the menu, despite being a leaf node, because Sam has direct
        # permission on it
        self.assertEqual(response.context['nodes'][1][1][0][1][0][0], Page.objects.get(id=6))
        self.client.logout()

        self.assertTrue(self.client.login(username='jane', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('wagtailadmin/shared/explorer_nav.html')
        self.assertEqual(len(response.context['nodes']), 1)
        self.assertEqual(response.context['nodes'][0][0], Page.objects.get(id=2))
        self.assertEqual(len(response.context['nodes'][0][1]), 0)

    def test_nonadmin_with_no_page_perms_sees_nothing_in_nav(self):
        self.assertTrue(self.client.login(username='mary', password='password'))
        response = self.client.get(reverse('wagtailadmin_explorer_nav'))

        self.assertEqual(response.status_code, 200)
        # Being in no Groups, Mary should ot be shown any nodes.
        self.assertEqual(len(response.context['nodes']), 0)
