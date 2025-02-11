from django.test import TestCase
from django.urls import reverse
import json

class TestAPIOrdering(TestCase):
    fixtures = ["demosite.json"]  

    def get_response(self, **params):
        return self.client.get(reverse("wagtailapi_v2:pages:listing"), params)
    
    def setUp(self):
        self.maxDiff = None 

    # BASIC TESTS

    def test_basic(self):
        response = self.get_response(order="title,first_published_at")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-type"], "application/json")

        content = json.loads(response.content.decode("UTF-8"))

        # Check that the meta section is there
        self.assertIn("meta", content)
        self.assertIsInstance(content["meta"], dict)

    def test_order_by_title_asc_then_first_published_desc(self):
        response = self.get_response(order="title,-first_published_at")
        self.assertEqual(response.status_code, 200)

        results = response.json()["items"]
        self.assertEqual(results, sorted(results, key=lambda x: (x["title"], -int(x["meta"]["first_published_at"] or 0))))

    def test_order_by_title_desc_then_first_published_desc(self):
        response = self.get_response(order="-title,-first_published_at")
        self.assertEqual(response.status_code, 200)

        results = response.json()["items"]
        self.assertEqual(results, sorted(results, key=lambda x: (-ord(x["title"][0]), -int(x["meta"]["first_published_at"] or 0))))

    def test_order_by_title_asc_then_first_published_asc(self):
        response = self.get_response(order="title,first_published_at")
        self.assertEqual(response.status_code, 200)

        results = response.json()["items"]
        self.assertEqual(results, sorted(results, key=lambda x: (x["title"], int(x["meta"]["first_published_at"] or 0))))

    def test_order_by_title_desc_then_first_published_asc(self):
        response = self.get_response(order="-title,first_published_at")
        self.assertEqual(response.status_code, 200)

        results = response.json()["items"]
        self.assertEqual(results, sorted(results, key=lambda x: (-ord(x["title"][0]), int(x["meta"]["first_published_at"] or 0))))
