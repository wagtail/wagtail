import hashlib
import pickle
import unittest
from io import BytesIO
from pathlib import Path

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils.text import slugify
from django.utils.translation import _trans
from django.utils.translation import gettext_lazy as _

from wagtail.coreutils import (
    InvokeViaAttributeShortcut,
    accepts_kwarg,
    camelcase_to_underscore,
    cautious_slugify,
    find_available_slug,
    get_content_languages,
    get_content_type_label,
    get_dummy_request,
    get_supported_content_language_variant,
    multigetattr,
    safe_snake_case,
    string_to_ascii,
)
from wagtail.models import Page, Site
from wagtail.utils.file import hash_filelike
from wagtail.utils.utils import deep_update


class TestCamelCaseToUnderscore(TestCase):
    def test_camelcase_to_underscore(self):
        test_cases = [
            ("HelloWorld", "hello_world"),
            ("longValueWithVarious subStrings", "long_value_with_various sub_strings"),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(camelcase_to_underscore(original), expected_result)


class TestStringToAscii(TestCase):
    def test_string_to_ascii(self):
        test_cases = [
            ("30 \U0001d5c4\U0001d5c6/\U0001d5c1", "30 km/h"),
            ("\u5317\u4EB0", "BeiJing"),
            ("ぁ あ ぃ い ぅ う ぇ", "a a i i u u e"),
            (
                "Ա Բ Գ Դ Ե Զ Է Ը Թ Ժ Ի Լ Խ Ծ Կ Հ Ձ Ղ Ճ Մ Յ Ն",
                "A B G D E Z E Y T' Zh I L Kh Ts K H Dz Gh Ch M Y N",
            ),
            ("Спорт!", "Sport!"),
            ("Straßenbahn", "Strassenbahn"),
            ("Hello world", "Hello world"),
            ("Ā ā Ă ă Ą ą Ć ć Ĉ ĉ Ċ ċ Č č Ď ď Đ", "A a A a A a C c C c C c C c D d D"),
            ("〔山脈〕", "[ShanMai]"),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(string_to_ascii(original), expected_result)


class TestCautiousSlugify(TestCase):
    def test_behaves_same_as_slugify_for_latin_chars(self):
        test_cases = [
            ("", ""),
            ("???", ""),
            ("Hello world", "hello-world"),
            ("Hello_world", "hello_world"),
            ("Hellö wörld", "hello-world"),
            ("Hello   world", "hello-world"),
            ("   Hello world   ", "hello-world"),
            ("Hello, world!", "hello-world"),
            ("Hello*world", "helloworld"),
            ("Hello☃world", "helloworld"),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(slugify(original), expected_result)
            self.assertEqual(cautious_slugify(original), expected_result)

    def test_escapes_non_latin_chars(self):
        test_cases = [
            ("Straßenbahn", "straxdfenbahn"),
            ("Спорт!", "u0421u043fu043eu0440u0442"),
            ("〔山脈〕", "u5c71u8108"),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(cautious_slugify(original), expected_result)


class TestSafeSnakeCase(TestCase):
    def test_strings_with_latin_chars(self):
        test_cases = [
            ("", ""),
            ("???", ""),
            ("using-Hyphen", "using_hyphen"),
            ("en–⁠dash", "endash"),  # unicode non-letter characters stripped
            ("  em—dash ", "emdash"),  # unicode non-letter characters stripped
            (
                "horizontal―BAR",
                "horizontalbar",
            ),  # unicode non-letter characters stripped
            ("Hello world", "hello_world"),
            ("Hello_world", "hello_world"),
            ("Hellö wörld", "hello_world"),
            ("Hello   world", "hello_world"),
            ("   Hello world   ", "hello_world"),
            ("Hello, world!", "hello_world"),
            ("Hello*world", "helloworld"),
            (
                "Screenshot_2020-05-29 Screenshot(1).png",
                "screenshot_2020_05_29_screenshot1png",
            ),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)

    def test_strings_with__non_latin_chars(self):
        test_cases = [
            ("Straßenbahn Straßenbahn", "straxdfenbahn_straxdfenbahn"),
            ("Сп орт!", "u0421u043f_u043eu0440u0442"),
        ]

        for (original, expected_result) in test_cases:
            self.assertEqual(safe_snake_case(original), expected_result)


class TestAcceptsKwarg(TestCase):
    def test_accepts_kwarg(self):
        def func_without_banana(apple, orange=42):
            pass

        def func_with_banana(apple, banana=42):
            pass

        def func_with_kwargs(apple, **kwargs):
            pass

        self.assertFalse(accepts_kwarg(func_without_banana, "banana"))
        self.assertTrue(accepts_kwarg(func_with_banana, "banana"))
        self.assertTrue(accepts_kwarg(func_with_kwargs, "banana"))


class TestTargetClass:
    """
    Used in TestInvokeViaAttributeShortcut (below)
    """

    def __init__(self):
        self.target_method_called_with = []

    def target_method(self, arg):
        self.target_method_called_with.append(arg)


class TestInvokeViaAttributeShortcut(SimpleTestCase):
    def setUp(self):
        self.target_object = TestTargetClass()
        self.test_object = InvokeViaAttributeShortcut(
            self.target_object, "target_method"
        )

    def test_basic(self):
        for value in ("foo", "bar", "baz"):
            # Use the shortcut to call the underlying method
            getattr(self.test_object, value)
            # Confirm that the underlying method was called
            self.assertIn(value, self.target_object.target_method_called_with)

    def test_pickleability(self):
        try:
            pickled = pickle.dumps(self.test_object, -1)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                "An error occured when attempting to pickle %r: %s"
                % (self.test_object, e)
            )
        try:
            self.test_object = pickle.loads(pickled)
        except Exception as e:  # noqa: BLE001
            raise AssertionError(
                "An error occured when attempting to unpickle %r: %s"
                % (self.test_object, e)
            )

        # Confirm unpickled object works the same
        self.target_object = self.test_object.obj
        self.test_basic()


class TestFindAvailableSlug(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(depth=1)
        self.home_page = Page.objects.get(depth=2)

        self.second_home_page = self.root_page.add_child(
            instance=Page(title="Second homepage", slug="home-1")
        )

    def test_find_available_slug(self):
        with self.assertNumQueries(1):
            slug = find_available_slug(self.root_page, "unique-slug")

        self.assertEqual(slug, "unique-slug")

    def test_find_available_slug_already_used(self):
        # Even though the first two slugs are already used, this still requires only one query to find a unique one
        with self.assertNumQueries(1):
            slug = find_available_slug(self.root_page, "home")

        self.assertEqual(slug, "home-2")

    def test_find_available_slug_ignore_page_id(self):
        with self.assertNumQueries(1):
            slug = find_available_slug(
                self.root_page, "home", ignore_page_id=self.second_home_page.id
            )

        self.assertEqual(slug, "home-1")


@override_settings(
    USE_I18N=True,
    WAGTAIL_I18N_ENABLED=True,
    LANGUAGES=[
        ("en", "English"),
        ("de", "German"),
        ("de-at", "Austrian German"),
        ("pt-br", "Portuguese (Brazil)"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("de", "German"),
        ("de-at", "Austrian German"),
        ("pt-br", "Portuguese (Brazil)"),
    ],
)
class TestGetContentLanguages(TestCase):
    def test_get_content_languages(self):
        self.assertEqual(
            get_content_languages(),
            {
                "de": "German",
                "de-at": "Austrian German",
                "en": "English",
                "pt-br": "Portuguese (Brazil)",
            },
        )

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("de", "German"),
        ],
    )
    def test_can_be_different_to_django_languages(self):
        self.assertEqual(
            get_content_languages(),
            {
                "de": "German",
                "en": "English",
            },
        )

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", _("English")),
            ("de", _("German")),
        ],
    )
    def test_can_be_a_translation_proxy(self):
        self.assertEqual(
            get_content_languages(),
            {
                "de": "German",
                "en": "English",
            },
        )

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("de", "German"),
            ("zh", "Chinese"),
        ],
    )
    def test_must_be_subset_of_django_languages(self):
        with self.assertRaises(ImproperlyConfigured) as e:
            get_content_languages()

        self.assertEqual(
            e.exception.args,
            (
                "The language zh is specified in WAGTAIL_CONTENT_LANGUAGES but not LANGUAGES. WAGTAIL_CONTENT_LANGUAGES must be a subset of LANGUAGES.",
            ),
        )


def TestGetContentTypeLabel(TestCase):
    def test_none(self):
        self.assertEqual(get_content_type_label(None), "Unknown content type")

    def test_valid_content_type(self):
        page_content_type = ContentType.objects.get_for_model(Page)
        self.assertEqual(get_content_type_label(page_content_type), "Page")

    def test_stale_content_type(self):
        stale_content_type = ContentType.objects.create(
            app_label="fake_app", model="deleted model"
        )
        self.assertEqual(get_content_type_label(stale_content_type), "Deleted model")


@override_settings(
    USE_I18N=True,
    WAGTAIL_I18N_ENABLED=True,
    LANGUAGES=[
        ("en", "English"),
        ("de", "German"),
        ("de-at", "Austrian German"),
        ("pt-br", "Portuguese (Brazil)"),
    ],
    WAGTAIL_CONTENT_LANGUAGES=[
        ("en", "English"),
        ("de", "German"),
        ("de-at", "Austrian German"),
        ("pt-br", "Portuguese (Brazil)"),
    ],
)
class TestGetSupportedContentLanguageVariant(TestCase):
    # From: https://github.com/django/django/blob/9e57b1efb5205bd94462e9de35254ec5ea6eb04e/tests/i18n/tests.py#L1481
    def test_get_supported_content_language_variant(self):
        g = get_supported_content_language_variant
        self.assertEqual(g("en"), "en")
        self.assertEqual(g("en-gb"), "en")
        self.assertEqual(g("de"), "de")
        self.assertEqual(g("de-at"), "de-at")
        self.assertEqual(g("de-ch"), "de")
        self.assertEqual(g("pt-br"), "pt-br")
        self.assertEqual(g("pt"), "pt-br")
        self.assertEqual(g("pt-pt"), "pt-br")
        with self.assertRaises(LookupError):
            g("pt", strict=True)
        with self.assertRaises(LookupError):
            g("pt-pt", strict=True)
        with self.assertRaises(LookupError):
            g("xyz")
        with self.assertRaises(LookupError):
            g("xy-zz")

    @override_settings(
        WAGTAIL_CONTENT_LANGUAGES=[
            ("en", "English"),
            ("de", "German"),
        ]
    )
    def test_uses_wagtail_content_languages(self):
        # be sure it's not using Django's LANGUAGES
        g = get_supported_content_language_variant
        self.assertEqual(g("en"), "en")
        self.assertEqual(g("en-gb"), "en")
        self.assertEqual(g("de"), "de")
        self.assertEqual(g("de-at"), "de")
        self.assertEqual(g("de-ch"), "de")
        with self.assertRaises(LookupError):
            g("pt-br")
        with self.assertRaises(LookupError):
            g("pt")
        with self.assertRaises(LookupError):
            g("pt-pt")
        with self.assertRaises(LookupError):
            g("xyz")
        with self.assertRaises(LookupError):
            g("xy-zz")


@override_settings(
    USE_I18N=False,
    WAGTAIL_I18N_ENABLED=False,
    WAGTAIL_CONTENT_LANGUAGES=None,
    LANGUAGE_CODE="en-us",
)
class TestGetSupportedContentLanguageVariantWithI18nFalse(TestCase):
    def setUp(self):
        # Need to forcibly clear the django.utils.translation._trans object when overriding
        # USE_I18N:
        # https://github.com/django/django/blob/3.1/django/utils/translation/__init__.py#L46-L48
        _trans.__dict__.clear()

    def tearDown(self):
        _trans.__dict__.clear()

    def test_lookup_language_with_i18n_false(self):
        # Make sure we can handle the 'null' USE_I18N=False implementation of
        # get_supported_language_variant returning 'en-us' rather than 'en',
        # despite 'en-us' not being in LANGUAGES.
        # https://github.com/wagtail/wagtail/issues/6539

        self.assertEqual(get_supported_content_language_variant("en-us"), "en")

    @override_settings(LANGUAGE_CODE="zz")
    def test_language_code_not_in_languages(self):
        # Ensure we can handle a LANGUAGE_CODE setting that isn't defined in LANGUAGES -
        # in this case get_content_languages has to cope with not being able to retrieve
        # a display name for the language
        self.assertEqual(get_supported_content_language_variant("zz"), "zz")
        self.assertEqual(get_supported_content_language_variant("zz-gb"), "zz")


class TestMultigetattr(TestCase):
    def setUp(self):
        class Thing:
            colour = "green"
            limbs = {"arms": 2, "legs": 3}

            def __init__(self):
                self.poke_was_called = False

            def speak(self):
                return "raaargh"

            def feed(self, food):
                return "gobble"

            def poke(self):
                self.poke_was_called = True
                raise Exception("don't do that")

            poke.alters_data = True

        self.thing = Thing()

    def test_multigetattr(self):
        self.assertEqual(multigetattr(self.thing, "colour"), "green")
        self.assertEqual(multigetattr(self, "thing.colour"), "green")
        self.assertEqual(multigetattr(self.thing, "limbs.arms"), 2)
        self.assertEqual(multigetattr(self.thing, "speak"), "raaargh")
        self.assertEqual(multigetattr(self, "thing.speak.0"), "r")

        with self.assertRaises(AttributeError):
            multigetattr(self.thing, "name")

        with self.assertRaises(AttributeError):
            multigetattr(self.thing, "limbs.antennae")

        with self.assertRaises(AttributeError):
            multigetattr(self.thing, "speak.999")

        with self.assertRaises(TypeError):
            multigetattr(self.thing, "feed")

        with self.assertRaises(SuspiciousOperation):
            multigetattr(self.thing, "poke")
        self.assertFalse(self.thing.poke_was_called)


class TestGetDummyRequest(TestCase):
    def test_standard_port(self):
        site = Site.objects.first()
        site.hostname = "other.example.com"
        site.port = 80
        site.save()

        request = get_dummy_request(site=site)
        self.assertEqual(request.get_host(), "other.example.com")

    def test_non_standard_port(self):
        site = Site.objects.first()
        site.hostname = "other.example.com"
        site.port = 8888
        site.save()

        request = get_dummy_request(site=site)
        self.assertEqual(request.get_host(), "other.example.com:8888")


class TestDeepUpdate(TestCase):
    def test_deep_update(self):
        val = {
            "captain": "picard",
            "beverage": {
                "type": "coffee",
                "temperature": "hot",
            },
        }

        deep_update(
            val,
            {
                "beverage": {
                    "type": "tea",
                    "variant": "earl grey",
                },
                "starship": "enterprise",
            },
        )

        self.assertEqual(
            val,
            {
                "captain": "picard",
                "beverage": {
                    "type": "tea",
                    "variant": "earl grey",
                    "temperature": "hot",
                },
                "starship": "enterprise",
            },
        )


class HashFileLikeTestCase(SimpleTestCase):
    test_file = Path.cwd() / "LICENSE"

    def test_hashes_io(self):
        self.assertEqual(
            hash_filelike(BytesIO(b"test")), "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3"
        )

    def test_hashes_file(self):
        with self.test_file.open(mode="rb") as f:
            self.assertEqual(
                hash_filelike(f), "9e58400061ca660ef7b5c94338a5205627c77eda"
            )

    def test_hashes_file_bytes(self):
        with self.test_file.open(mode="rb") as f:
            self.assertEqual(
                hash_filelike(f), "9e58400061ca660ef7b5c94338a5205627c77eda"
            )

    def test_hashes_django_uploaded_file(self):
        """
        Check Django's file shims can be hashed as-is.
        `SimpleUploadedFile` inherits the base `UploadedFile`, but is easiest to test against
        """
        self.assertEqual(
            hash_filelike(SimpleUploadedFile("example.txt", b"test")),
            "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3",
        )

    @unittest.skipIf(
        hasattr(hashlib, "file_digest"),
        reason="`file_digest` doesn't support this interface",
    )
    def test_hashes_large_file(self):
        class FakeLargeFile:
            """
            A class that pretends to be a huge file (~1.3GB)
            """

            def __init__(self):
                self.iterations = 5000

            def read(self, bytes):
                self.iterations -= 1
                if not self.iterations:
                    return b""

                return b"A" * bytes

        self.assertEqual(
            hash_filelike(FakeLargeFile()),
            "bd36f0c5a02cd6e9e34202ea3ff8db07b533e025",
        )
