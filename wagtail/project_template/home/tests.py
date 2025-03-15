from wagtail.test.utils import WagtailPageTestCase
from wagtail.models import Page
from home.models import HomePage

class HomeSetUpTests(WagtailPageTestCase):
    """
    Tests steps needed by follow up tests
    """

    def test_root_create(self):
        root_page = Page.objects.get(pk=1)
        self.assertIsNotNone(root_page) 

    def test_homepage_create(self):
        root_page = Page.objects.get(pk=1)
        homepage = HomePage(title="Home")
        root_page.add_child(instance=homepage)
        self.assertTrue(HomePage.objects.filter(title="Home").exists())


class HomeTests(WagtailPageTestCase):
    """
    Class for testing homepage logic
    """

    def setUp(self):
        """
        Set up the testing environment.
        """

        root_page = Page.objects.get(pk=1)
        self.homepage = HomePage(title='Home')
        root_page.add_child(instance=self.homepage)
        
    def test_your_test(self):
        """
        Tests if BlogIndexPage can be created.
        """

        raise NotImplementedError("The tests are not implemented yet.")