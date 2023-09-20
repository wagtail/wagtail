import os

from django.contrib.messages import constants as message_constants
from django.utils.translation import gettext_lazy as _

DEBUG = False
WAGTAIL_ROOT = os.path.dirname(os.path.dirname(__file__))
WAGTAILADMIN_BASE_URL = "http://testserver"
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, "tests", "test-static")
MEDIA_ROOT = os.path.join(WAGTAIL_ROOT, "tests", "test-media")
MEDIA_URL = "/media/"

TIME_ZONE = "Asia/Tokyo"

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DATABASE_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DATABASE_NAME", ":memory:"),
        "USER": os.environ.get("DATABASE_USER", ""),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", ""),
        "PORT": os.environ.get("DATABASE_PORT", ""),
        "TEST": {"NAME": os.environ.get("DATABASE_NAME", "")},
    }
}

# Set regular database name when a non-SQLite db is used
if DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
    DATABASES["default"]["NAME"] = os.environ.get("DATABASE_NAME", "wagtail")

# Add extra options when mssql is used (on for example appveyor)
if DATABASES["default"]["ENGINE"] == "sql_server.pyodbc":
    DATABASES["default"]["OPTIONS"] = {
        "driver": os.environ.get("DATABASE_DRIVER", "SQL Server Native Client 11.0"),
        "MARS_Connection": "True",
        "host_is_server": True,  # Applies to FreeTDS driver only
    }


# explicitly set charset / collation to utf8 on mysql
if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["TEST"]["CHARSET"] = "utf8"
    DATABASES["default"]["TEST"]["COLLATION"] = "utf8_general_ci"


SECRET_KEY = "not needed"

ROOT_URLCONF = "wagtail.test.urls"

STATIC_URL = "/static/"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

# Default storage settings
# https://docs.djangoproject.com/en/stable/ref/settings/#std-setting-STORAGES
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

if os.environ.get("STATICFILES_STORAGE", "") == "manifest":
    STORAGES["staticfiles"][
        "BACKEND"
    ] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

    # DJANGO_VERSION < 4.2
    STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
    )


USE_TZ = not os.environ.get("DISABLE_TIMEZONE")
if not USE_TZ:
    print("Timezone support disabled")  # noqa: T201

LANGUAGE_CODE = "en"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.request",
                "wagtail.test.context_processors.do_not_use_static_url",
                "wagtail.contrib.settings.context_processors.settings",
            ],
            "debug": True,  # required in order to catch template errors
        },
    },
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "APP_DIRS": False,
        "DIRS": [
            os.path.join(WAGTAIL_ROOT, "test", "testapp", "jinja2_templates"),
        ],
        "OPTIONS": {
            "extensions": [
                "wagtail.jinja2tags.core",
                "wagtail.admin.jinja2tags.userbar",
                "wagtail.images.jinja2tags.images",
                "wagtail.contrib.settings.jinja2tags.settings",
            ],
        },
    },
]

MIDDLEWARE = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "wagtail.test.middleware.BlockDodgyUserAgentMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
)

INSTALLED_APPS = [
    # Install wagtailredirects with its appconfig
    # There's nothing special about wagtailredirects, we just need to have one
    # app which uses AppConfigs to test that hooks load properly
    "wagtail.contrib.redirects.apps.WagtailRedirectsAppConfig",
    "wagtail.test.testapp",
    "wagtail.test.demosite",
    "wagtail.test.snippets",
    "wagtail.test.routablepage",
    "wagtail.test.search",
    "wagtail.test.modeladmintest",
    "wagtail.test.i18n",
    "wagtail.test.streamfield_migrations",
    "wagtail.contrib.simple_translation",
    "wagtail.contrib.styleguide",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.frontend_cache",
    "wagtail.contrib.search_promotions",
    "wagtail.contrib.settings",
    "wagtail.contrib.modeladmin",
    "wagtail.contrib.table_block",
    "wagtail.contrib.forms",
    "wagtail.contrib.typed_table_block",
    "wagtail.search",
    "wagtail.embeds",
    "wagtail.images",
    "wagtail.sites",
    "wagtail.locales",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.admin",
    "wagtail.api.v2",
    "wagtail",
    "taggit",
    "rest_framework",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
]


# Using DatabaseCache to make sure that the cache is cleared between tests.
# This prevents false-positives in some wagtail core tests where we are
# changing the 'wagtail_root_paths' key which may cause future tests to fail.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache",
    }
}

PASSWORD_HASHERS = (
    "django.contrib.auth.hashers.MD5PasswordHasher",  # don't use the intentionally slow default password hasher
)

ALLOWED_HOSTS = ["localhost", "testserver", "other.example.com"]

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database.fallback",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if os.environ.get("USE_EMAIL_USER_MODEL"):
    INSTALLED_APPS.append("wagtail.test.emailuser")
    AUTH_USER_MODEL = "emailuser.EmailUser"
    print("EmailUser (no username) user model active")  # noqa: T201
else:
    INSTALLED_APPS.append("wagtail.test.customuser")
    AUTH_USER_MODEL = "customuser.CustomUser"
    # Extra user field for custom user edit and create form tests. This setting
    # needs to here because it is used at the module level of wagtailusers.forms
    # when the module gets loaded. The decorator 'override_settings' does not work
    # in this scenario.
    WAGTAIL_USER_CUSTOM_FIELDS = ["country", "attachment"]

if os.environ.get("DATABASE_ENGINE") == "django.db.backends.postgresql":
    WAGTAILSEARCH_BACKENDS["postgresql"] = {
        "BACKEND": "wagtail.search.backends.database",
        "AUTO_UPDATE": False,
        "SEARCH_CONFIG": "english",
    }

if "ELASTICSEARCH_URL" in os.environ:
    if os.environ.get("ELASTICSEARCH_VERSION") == "8":
        backend = "wagtail.search.backends.elasticsearch8"
    elif os.environ.get("ELASTICSEARCH_VERSION") == "7":
        backend = "wagtail.search.backends.elasticsearch7"
    elif os.environ.get("ELASTICSEARCH_VERSION") == "6":
        backend = "wagtail.search.backends.elasticsearch6"
    elif os.environ.get("ELASTICSEARCH_VERSION") == "5":
        backend = "wagtail.search.backends.elasticsearch5"

    WAGTAILSEARCH_BACKENDS["elasticsearch"] = {
        "BACKEND": backend,
        "URLS": [os.environ["ELASTICSEARCH_URL"]],
        "TIMEOUT": 10,
        "max_retries": 1,
        "AUTO_UPDATE": False,
        "INDEX_SETTINGS": {"settings": {"index": {"number_of_shards": 1}}},
    }


WAGTAIL_SITE_NAME = "Test Site"

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    "default": {"WIDGET": "wagtail.admin.rich_text.DraftailRichTextArea"},
    "custom": {"WIDGET": "wagtail.test.testapp.rich_text.CustomRichTextArea"},
}

WAGTAIL_CONTENT_LANGUAGES = [
    ("en", _("English")),
    ("fr", _("French")),
]


# Set a non-standard DEFAULT_AUTHENTICATION_CLASSES value, to verify that the
# admin API still works with session-based auth regardless of this setting
# (see https://github.com/wagtail/wagtail/issues/5585)
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
    ]
}

# Disable redirect autocreation for the majority of tests (to improve efficiency)
WAGTAILREDIRECTS_AUTO_CREATE = False


# https://github.com/wagtail/wagtail/issues/2551 - projects should be able to set
# MESSAGE_TAGS for their own purposes without them leaking into Wagtail admin styles.

MESSAGE_TAGS = {
    message_constants.DEBUG: "my-custom-tag",
    message_constants.INFO: "my-custom-tag",
    message_constants.SUCCESS: "my-custom-tag",
    message_constants.WARNING: "my-custom-tag",
    message_constants.ERROR: "my-custom-tag",
}
