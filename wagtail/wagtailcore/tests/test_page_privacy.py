from django.test import TestCase
from wagtail.wagtailcore.models import Page, PageViewRestriction


class TestPagePrivacy(TestCase):
    fixtures = ['test.json']

    def setUp(self):
        self.secret_plans_page = Page.objects.get(url_path='/home/secret-plans/')
        self.view_restriction = PageViewRestriction.objects.get(
            page=self.secret_plans_page)

    def test_anonymous_user_must_authenticate(self):
        response = self.client.get('/secret-plans/')
        self.assertEqual(response.templates[0].name, 'wagtailcore/password_required.html')

        submit_url = "/_util/authenticate_with_password/%d/%d/" % (self.view_restriction.id, self.secret_plans_page.id)
        self.assertContains(response, '<form action="%s"' % submit_url)
        self.assertContains(
            response,
            '<input id="id_return_url" name="return_url" type="hidden" value="/secret-plans/" />'
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
            '<input id="id_return_url" name="return_url" type="hidden" value="/secret-plans/steal-underpants/" />'
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
