import json
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.testapp.models import SimplePage

from .utils import AdminAPITestCase


class TestExplorerPagesApi(AdminAPITestCase):

    def get_response(self, **params):
        return self.client.get(reverse('wagtailadmin_api_for_explorer:pages:listing'), params)

    def get_page_id_list(self, content):
        return [page['id'] for page in content['items']]

    def make_simple_page(self, parent, title):
        return parent.add_child(instance=SimplePage(title=title, content='Simple page'))

    def test_filter(self):
        movies = self.make_simple_page(Page.objects.get(pk=1), 'Movies')
        visible_movies = [
            self.make_simple_page(movies, 'The Way of the Dragon'),
            self.make_simple_page(movies, 'Enter the Dragon'),
            self.make_simple_page(movies, 'Dragons Forever'),
        ]

        # These will be filtered out
        self.make_simple_page(movies, 'The Hidden Fortress')
        self.make_simple_page(movies, 'Crouching Tiger, Hidden Dragon')
        self.make_simple_page(movies, 'Crouching Tiger, Hidden Dragon: Sword of Destiny')

        response = self.get_response(child_of=movies.pk)
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [page.pk for page in visible_movies])

        # Now test with ?type= filter, so we can check that the filtering logic works with specific querysets
        response = self.get_response(child_of=movies.pk, type='tests.SimplePage')
        content = json.loads(response.content.decode('UTF-8'))
        page_id_list = self.get_page_id_list(content)
        self.assertEqual(page_id_list, [page.pk for page in visible_movies])

    def test_no_child_of(self):
        response = self.get_response()
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode('UTF-8'))
        self.assertEqual(content, {
            'message': 'calling explorer API without child_of is not supported',
        })
