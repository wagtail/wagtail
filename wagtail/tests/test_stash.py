from django.test import SimpleTestCase

from wagtail.utils.stash import (
    clear,
    enabled,
    get,
    get_or_set,
    set,
    stash_scope,
)


class TestStash(SimpleTestCase):
    def test_disabled_outside_scope(self):
        self.assertFalse(enabled(scope="wagtail"))
        self.assertIsNone(get("k", scope="wagtail"))
        set("k", "v", scope="wagtail")
        self.assertIsNone(get("k", scope="wagtail"))
        self.assertEqual(get_or_set("k", lambda: "loaded", scope="wagtail"), "loaded")
        self.assertIsNone(get("k", scope="wagtail"))

    def test_get_or_set_reuses_value_inside_scope(self):
        calls = []

        def load():
            calls.append(1)
            return "site"

        with stash_scope("wagtail"):
            self.assertTrue(enabled(scope="wagtail"))
            self.assertEqual(get_or_set("k", load, scope="wagtail"), "site")
            self.assertEqual(get_or_set("k", load, scope="wagtail"), "site")
            self.assertEqual(get("k", scope="wagtail"), "site")
        self.assertEqual(calls, [1])
        self.assertFalse(enabled(scope="wagtail"))
        self.assertIsNone(get("k", scope="wagtail"))

    def test_clear_key_and_nested_scopes(self):
        with stash_scope("wagtail"):
            set("a", 1, scope="wagtail")
            set("b", 2, scope="wagtail")
            with stash_scope("wagtail"):
                set("a", 3, scope="wagtail")
                self.assertEqual(get("a", scope="wagtail"), 3)
                self.assertEqual(get("b", scope="wagtail"), 2)
            self.assertEqual(get("a", scope="wagtail"), 1)
            clear("a", scope="wagtail")
            self.assertIsNone(get("a", scope="wagtail"))
            self.assertEqual(get("b", scope="wagtail"), 2)
