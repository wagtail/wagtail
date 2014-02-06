from django.test import TestCase

import models
from search import Search


class TestSearch(TestCase):
    def test_search(self):
        # Create search interface and reset the index
        s = Search()
        s.reset_index()

        # Create a couple of objects and add them to the index
        testa = models.SearchTest()
        testa.title = "Hello World"
        testa.save()
        s.add(testa)

        testb = models.SearchTest()
        testb.title = "Hello"
        testb.save()
        s.add(testb)

        testc = models.SearchTestChild()
        testc.title = "Hello"
        testc.save()
        s.add(testc)

        # Refresh index
        s.refresh_index()

        # Ordinary search
        results = s.search("Hello", models.SearchTest)
        self.assertEqual(len(results), 3)

          # Ordinary search on "World"
        results = s.search("World", models.SearchTest)
        self.assertEqual(len(results), 1)

        # Searcher search
        results = models.SearchTest.title_search("Hello")
        self.assertEqual(len(results), 3)

        # Ordinary search on child
        results = s.search("Hello", models.SearchTestChild)
        self.assertEqual(len(results), 1)

        # Searcher search on child
        results = models.SearchTestChild.title_search("Hello")
        self.assertEqual(len(results), 1)
