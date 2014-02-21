from django.test import TestCase
from django.contrib.auth.models import User


class TestPageSearch(TestCase):
    def test_root_can_appear_in_search_results(self):
        User.objects.create_superuser(username='test', email='test@email.com', password='password')
        self.client.login(username='test', password='password')

        response = self.client.get('/admin/pages/search/?q=roo')
        self.assertEqual(response.status_code, 200)
        # 'pages' list in the response should contain root
        results = response.context['pages']
        self.assertTrue(any([r.slug == 'root' for r in results]))
