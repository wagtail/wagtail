from .settings import *  # noqa

# Settings meant to run the test suite with Django’s development server, for integration tests.
DEBUG = True

DATABASES["default"]["NAME"] = "ui_tests.db"  # noqa

INSTALLED_APPS += [  # noqa
    "pattern_library",
]

# Allow loopback address to access the server without DNS resolution (lack of Happy Eyeballs in Node 18).
ALLOWED_HOSTS += ["127.0.0.1"]  # noqa

TEMPLATES[0]["OPTIONS"]["builtins"] = ["pattern_library.loader_tags"]  # noqa

PATTERN_LIBRARY = {
    # Groups of templates for the pattern library navigation. The keys
    # are the group titles and the values are lists of template name prefixes that will
    # be searched to populate the groups.
    "SECTIONS": (
        (
            "components",
            ["wagtailadmin/shared", "wagtailadmin/panels", "wagtailadmin/home"],
        ),
    ),
    # Configure which files to detect as templates.
    "TEMPLATE_SUFFIX": ".html",
    "PATTERN_BASE_TEMPLATE_NAME": "",
    "BASE_TEMPLATE_NAMES": [],
}
