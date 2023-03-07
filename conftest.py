import os
import shutil
import warnings

import django

# This function adds command line options to pytest.
def pytest_addoption(parser):
    parser.addoption(
        "--deprecation",
        choices=["all", "pending", "imminent", "none"],
        default="pending",
    )
    parser.addoption("--postgres", action="store_true")
    parser.addoption("--elasticsearch", action="store_true")

# This function configures pytest with the provided options.
def pytest_configure(config):
    # Get the chosen deprecation level from the command line arguments.
    deprecation = config.getoption("deprecation")

    # Filter deprecation warnings from Wagtail based on the chosen level.
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

    # If the --postgres option is provided, set the DATABASE_ENGINE environment variable.
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

# This function cleans up after pytest finishes.
def pytest_unconfigure(config):
    from wagtail.test.settings import MEDIA_ROOT, STATIC_ROOT

    shutil.rmtree(STATIC_ROOT, ignore_errors=True)
    shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
