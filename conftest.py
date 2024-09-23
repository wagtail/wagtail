import os
import shutil
import warnings

import django


def pytest_addoption(parser):
    parser.addoption(
        "--deprecation",
        choices=["all", "pending", "imminent", "none"],
        default="pending",
    )
    parser.addoption("--postgres", action="store_true")
    parser.addoption("--elasticsearch", action="store_true")


def pytest_configure(config):
    deprecation = config.getoption("deprecation")

    only_wagtail = r"^wagtail(\.|$)"
    if deprecation == "all":
        # Show all deprecation warnings from all packages
        warnings.simplefilter("default", DeprecationWarning)
        warnings.simplefilter("default", PendingDeprecationWarning)
    elif deprecation == "pending":
        # Show all deprecation warnings from wagtail
        warnings.filterwarnings(
            "default", category=DeprecationWarning, module=only_wagtail
        )
        warnings.filterwarnings(
            "default", category=PendingDeprecationWarning, module=only_wagtail
        )
    elif deprecation == "imminent":
        # Show only imminent deprecation warnings from wagtail
        warnings.filterwarnings(
            "default", category=DeprecationWarning, module=only_wagtail
        )
    elif deprecation == "none":
        # Deprecation warnings are ignored by default
        pass

    if config.getoption("postgres"):
        os.environ["DATABASE_ENGINE"] = "django.db.backends.postgresql"

    # Setup django after processing the pytest arguments so that the env
    # variables are available in the settings
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wagtail.test.settings")
    django.setup()

    # Activate a language: This affects HTTP header HTTP_ACCEPT_LANGUAGE sent by
    # the Django test client.
    from django.utils import translation

    translation.activate("en")

    from wagtail.test.settings import MEDIA_ROOT, STATIC_ROOT

    shutil.rmtree(STATIC_ROOT, ignore_errors=True)
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)


def pytest_unconfigure(config):
    from wagtail.test.settings import MEDIA_ROOT, STATIC_ROOT

    shutil.rmtree(STATIC_ROOT, ignore_errors=True)
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
