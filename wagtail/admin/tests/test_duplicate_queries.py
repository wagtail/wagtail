from collections import Counter

from django.db import DEFAULT_DB_ALIAS, connections
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from wagtail.core.models import Page
from wagtail.tests.utils import WagtailTestUtils


class _AssertNumDuplicateQueriesContext(CaptureQueriesContext):
    def __init__(self, test_case, num, connection):
        self.test_case = test_case
        self.num = num
        super().__init__(connection)

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        if exc_type is not None:
            return

        counter = Counter(query["sql"] for query in self)
        duplicates = {
            duplicate: duplicate_count
            for duplicate, duplicate_count in counter.items()
            if duplicate_count > 1
        }
        duplicates = dict(
            sorted(duplicates.items(), key=lambda item: item[1], reverse=True)
        )

        self.test_case.assertEqual(
            len(duplicates),
            self.num,
            f"\n{len(duplicates)} duplicate queries:, {self.num} expected\n"
            + "\n".join(
                [
                    f"Repeated {duplicate_count} times:\n{duplicate}\n"
                    for duplicate, duplicate_count in duplicates.items()
                ]
            ),
        )


class TestDuplicateQueries(TestCase, WagtailTestUtils):
    fixtures = ["test.json"]

    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.events_index = Page.objects.get(url_path="/home/events/")
        self.christmas_page = Page.objects.get(url_path="/home/events/christmas/")
        self.user = self.login()

    def get(self, name, args):
        return self.client.get(reverse(name, args=args))

    def test_duplicate_queries(self):
        views = (
            ("wagtailadmin_explore", (self.root_page.id,)),
            ("wagtailadmin_pages:add", ("tests", "simplepage", self.root_page.id)),
            ("wagtailadmin_pages:edit", (self.events_index.id,)),
            ("wagtailadmin_pages:move", (self.events_index.id,)),
            ("wagtailadmin_pages:search", {}),
            ("wagtailadmin_pages:revisions_index", (self.christmas_page.id,)),
            ("wagtailadmin_pages:delete", (self.events_index.id,)),
        )
        for name, args in views:
            with self.subTest(name=name):
                self.assertNumDuplicateQueries(0, self.get, name=name, args=args)

    def assertNumDuplicateQueries(self, num=0, func=None, *args, using=DEFAULT_DB_ALIAS, **kwargs):
        conn = connections[using]

        context = _AssertNumDuplicateQueriesContext(self, num, conn)
        if func is None:
            return context

        with context:
            func(*args, **kwargs)
