from django.test import TestCase
from wagtail.actions.create_alias import CreatePageAliasAction, CreatePageAliasIntegrityError, CreatePageAliasPermissionError
from wagtail.models import Page
from wagtail.test.utils import WagtailTestUtils

class TestCreatePageAliasAction(TestCase, WagtailTestUtils):
    def setUp(self):
        self.user = self.create_user(username='testuser', password='password', is_superuser=True)
        self.root_page = Page.objects.get(id=1)
        self.page = Page(title="Test Page", slug="test-page")
        self.root_page.add_child(instance=self.page)
        self.action = CreatePageAliasAction(page=self.page, user=self.user)

    def test_check_cd1v_cd2v_cd3v(self):
        self.action.recursive = True
        self.action.page = self.root_page
        with self.assertRaises(CreatePageAliasIntegrityError):
            self.action.check()

    def test_check_cd1v_cd2v_cd3f(self):
        self.action.recursive = True
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        with self.assertRaises(CreatePageAliasIntegrityError):
            self.action.check()

    def test_check_cd1v_cd2f_cd3v(self):
        self.action.recursive = True
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.page.add_child(instance=parent)
        self.action.page = parent
        with self.assertRaises(CreatePageAliasIntegrityError):
            self.action.check()

    def test_check_cd1v_cd2f_cd3f(self):
        self.action.recursive = True
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        try:
            self.action.check()
        except CreatePageAliasIntegrityError:
            self.fail("CreatePageAliasIntegrityError raised unexpectedly!")

    def test_check_cd4v_cd5v_cd6v(self):
        self.action.recursive = False
        self.action.skip_permission_checks = False
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        self.action.user = self.create_user(username='user', password='password')
        with self.assertRaises(CreatePageAliasPermissionError):
            self.action.check()

    def test_check_cd4v_cd5v_cd6f(self):
        self.action.recursive = False
        self.action.skip_permission_checks = False
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        self.action.user = self.user
        try:
            self.action.check()
        except CreatePageAliasPermissionError:
            self.fail("CreatePageAliasPermissionError raised unexpectedly!")

    def test_check_cd4v_cd5f(self):
        self.action.recursive = False
        self.action.skip_permission_checks = True
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        self.action.user = self.user
        try:
            self.action.check()
        except CreatePageAliasPermissionError:
            self.fail("CreatePageAliasPermissionError raised unexpectedly!")

    def test_check_cd4f(self):
        self.action.recursive = False
        self.action.user = None
        parent = Page(title="Parent Page", slug="parent-page")
        self.root_page.add_child(instance=parent)
        self.action.page = parent
        try:
            self.action.check()
        except CreatePageAliasPermissionError:
            self.fail("CreatePageAliasPermissionError raised unexpectedly!")
