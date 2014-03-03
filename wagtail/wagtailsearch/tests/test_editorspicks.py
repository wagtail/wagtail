from django.test import TestCase
from wagtail.tests.utils import login
from wagtail.wagtailsearch import models


class TestEditorsPicks(TestCase):
    def test_editors_pick_create(self):
        # Create an editors pick to the root page
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First editors pick",
        )

        # Check
        self.assertEqual(models.Query.get("root page").editors_picks.count(), 1)
        self.assertEqual(models.Query.get("root page").editors_picks.first().page_id, 1)

    def test_editors_pick_ordering(self):
        # Add 3 editors picks in a different order to their sort_order values
        # They should be ordered by their sort order values and not their insertion order
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=0,
            description="First editors pick",
        )
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=2,
            description="Last editors pick",
        )
        models.EditorsPick.objects.create(
            query=models.Query.get("root page"),
            page_id=1,
            sort_order=1,
            description="Middle editors pick",
        )

        # Check
        self.assertEqual(models.Query.get("root page").editors_picks.count(), 3)
        self.assertEqual(models.Query.get("root page").editors_picks.first().description, "First editors pick")
        self.assertEqual(models.Query.get("root page").editors_picks.last().description, "Last editors pick")


class TestEditorsPicksIndexView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/', params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)

    def test_search(self):
        response = self.get({'q': "Hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query_string'], "Hello")

    def test_pagination(self):
        pages = ['0', '1', '-1', '9999', 'Not a page']
        for page in pages:
            response = self.get({'p': page})
            self.assertEqual(response.status_code, 200)


class TestEditorsPicksAddView(TestCase):
    def setUp(self):
        login(self.client)

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/add/', params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestEditorsPicksEditView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an editors pick to edit
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/', params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)


class TestEditorsPicksDeleteView(TestCase):
    def setUp(self):
        login(self.client)

        # Create an editors pick to delete
        self.query = models.Query.get("Hello")
        self.query.editors_picks.create(page_id=1, description="Root page")

    def get(self, params={}):
        return self.client.get('/admin/search/editorspicks/' + str(self.query.id) + '/delete/', params)

    def test_status_code(self):
        self.assertEqual(self.get().status_code, 200)
