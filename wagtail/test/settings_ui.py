from .settings import *  # noqa: F403

# Settings meant to run the test suite with Django’s development server, for integration tests.

DATABASES["default"]["NAME"] = "ui_tests.db"  # noqa: F405

INSTALLED_APPS += [  # noqa: F405
    "pattern_library",
]

TEMPLATES[0]["OPTIONS"]["builtins"] = ["pattern_library.loader_tags"]  # noqa: F405

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

DEBUG = True
