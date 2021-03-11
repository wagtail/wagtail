from django.contrib.auth.models import Group
from django.test import TestCase

from wagtail.core.models import Page, PageViewRestriction
from wagtail.tests.utils import WagtailTestUtils


class TestPagePrivacy(TestCase, WagtailTestUtils):
    fixtures = ['test.json']

    def setUp(self):
        self.secret_plans_page = Page.objects.get(url_path='/home/secret-plans/')
        self.view_restriction = PageViewRestriction.objects.get(
            page=self.secret_plans_page)

        self.secret_event_editor_plans_page = Page.objects.get(url_path='/home/secret-event-editor-plans/')
        self.event_editors_group = Group.objects.get(name='Event editors')
        self.secret_login_plans_page = Page.objects.get(url_path='/home/secret-login-plans/')

    def test_anonymous_user_must_authenticate(self):
        response = self.client.get('/secret-plans/')
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')

        submit_url = "/_util/authenticate_with_password/%d/%d/" % (self.view_restriction.id, self.secret_plans_page.id)
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="/secret-plans/" />',
            html=True
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(submit_url, {
            'password': 'wrongpassword',
            'return_url': '/secret-plans/',
        })
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')
        self.assertContains(response, '<form action="%s"' % submit_url)

        # posting the correct password should redirect back to return_url
        response = self.client.post(submit_url, {
            'password': 'swordfish',
            'return_url': '/secret-plans/',
        })
        self.assertRedirects(response, '/secret-plans/')

        # now requests to /secret-plans/ should pass authentication
        response = self.client.get('/secret-plans/')
        self.assertEqual(response.templates[0].name, 'tests/simple_page.html')

        self.client.logout()

        # posting an invalid return_url will redirect to default login redirect
        with self.settings(LOGIN_REDIRECT_URL='/'):
            response = self.client.post(submit_url, {
                'password': 'swordfish',
                'return_url': 'https://invaliddomain.com',
            })
            self.assertRedirects(response, '/')

    def test_view_restrictions_apply_to_subpages(self):
        underpants_page = Page.objects.get(url_path='/home/secret-plans/steal-underpants/')
        response = self.client.get('/secret-plans/steal-underpants/')

        # check that we're overriding the default password_required template for this page type
        self.assertEqual(response.templates[0].name, 'tests/event_page_password_required.html')

        submit_url = "/_util/authenticate_with_password/%d/%d/" % (self.view_restriction.id, underpants_page.id)
        self.assertContains(response, '<title>Steal underpants</title>')
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="/secret-plans/steal-underpants/" />',
            html=True
        )

        # posting the wrong password should redisplay the password page
        response = self.client.post(submit_url, {
            'password': 'wrongpassword',
            'return_url': '/secret-plans/steal-underpants/',
        })
        self.assertEqual(response.templates[0].name, 'tests/event_page_password_required.html')
        self.assertContains(response, '<form action="%s"' % submit_url)

        # posting the correct password should redirect back to return_url
        response = self.client.post(submit_url, {
            'password': 'swordfish',
            'return_url': '/secret-plans/steal-underpants/',
        })
        self.assertRedirects(response, '/secret-plans/steal-underpants/')

        # now requests to /secret-plans/ should pass authentication
        response = self.client.get('/secret-plans/steal-underpants/')
        self.assertEqual(response.templates[0].name, 'tests/event_page.html')

    def test_view_restrictions_apply_to_aliases(self):
        secret_plans_page = Page.objects.get(url_path='/home/secret-plans/')
        secret_plans_alias_page = secret_plans_page.create_alias(update_slug='alias-secret-plans')

        response = self.client.get('/alias-secret-plans/')

        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')

        submit_url = "/_util/authenticate_with_password/%d/%d/" % (self.view_restriction.id, secret_plans_alias_page.id)
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="/alias-secret-plans/" />',
            html=True
        )

    def test_view_restrictions_apply_to_subpages_of_aliases(self):
        secret_plans_page = Page.objects.get(url_path='/home/secret-plans/')
        secret_plans_alias_page = secret_plans_page.create_alias(update_slug='alias-secret-plans')

        underpants_page = Page.objects.get(url_path='/home/secret-plans/steal-underpants/')
        underpants_alias_page = underpants_page.create_alias(parent=secret_plans_alias_page)

        response = self.client.get('/alias-secret-plans/steal-underpants/')

        # check that we're overriding the default password_required template for this page type
        self.assertEqual(response.templates[0].name, 'tests/event_page_password_required.html')

        submit_url = "/_util/authenticate_with_password/%d/%d/" % (self.view_restriction.id, underpants_alias_page.id)
        self.assertContains(response, '<title>Steal underpants</title>')
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="/alias-secret-plans/steal-underpants/" />',
            html=True
        )

    def test_group_restriction_with_anonymous_user(self):
        response = self.client.get('/secret-event-editor-plans/')
        self.assertRedirects(response, '/_util/login/?next=/secret-event-editor-plans/')

    def test_group_restriction_with_unpermitted_user(self):
        self.login(username='eventmoderator', password='password')
        response = self.client.get('/secret-event-editor-plans/')
        self.assertRedirects(response, '/_util/login/?next=/secret-event-editor-plans/')

    def test_group_restriction_with_permitted_user(self):
        self.login(username='eventeditor', password='password')
        response = self.client.get('/secret-event-editor-plans/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Secret event editor plans</title>")

    def test_group_restriction_with_superuser(self):
        self.login(username='superuser', password='password')
        response = self.client.get('/secret-event-editor-plans/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Secret event editor plans</title>")

    def test_login_restriction_with_anonymous_user(self):
        response = self.client.get('/secret-login-plans/')
        self.assertRedirects(response, '/_util/login/?next=/secret-login-plans/')

    def test_login_restriction_with_logged_in_user(self):
        self.login(username='eventmoderator', password='password')
        response = self.client.get('/secret-login-plans/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Secret login plans</title>")
