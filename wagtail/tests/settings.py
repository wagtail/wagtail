import os

DEBUG = False
WAGTAIL_ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_ROOT = os.path.join(WAGTAIL_ROOT, 'tests', 'test-static')
MEDIA_ROOT = os.path.join(WAGTAIL_ROOT, 'tests', 'test-media')
MEDIA_URL = '/media/'

TIME_ZONE = 'Asia/Tokyo'

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DATABASE_NAME', 'wagtail'),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_PASS', None),
        'HOST': os.environ.get('DATABASE_HOST', None),

        'TEST': {
            'NAME': os.environ.get('DATABASE_NAME', None),
        }
    }
}

# Add extra options when mssql is used (on for example appveyor)
if DATABASES['default']['ENGINE'] == 'sql_server.pyodbc':
    DATABASES['default']['OPTIONS'] = {
        'driver': 'SQL Server Native Client 11.0',
        'MARS_Connection': 'True',
    }


# explicitly set charset / collation to utf8 on mysql
if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    DATABASES['default']['TEST']['CHARSET'] = 'utf8'
    DATABASES['default']['TEST']['COLLATION'] = 'utf8_general_ci'


SECRET_KEY = 'not needed'

ROOT_URLCONF = 'wagtail.tests.urls'

STATIC_URL = '/static/'
STATIC_ROOT = STATIC_ROOT

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

USE_TZ = True

LANGUAGE_CODE = "en"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'wagtail.tests.context_processors.do_not_use_static_url',
                'wagtail.contrib.settings.context_processors.settings',
            ],
            'debug': True,  # required in order to catch template errors
        },
    },
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'APP_DIRS': False,
        'DIRS': [
            os.path.join(WAGTAIL_ROOT, 'tests', 'testapp', 'jinja2_templates'),
        ],
        'OPTIONS': {
            'extensions': [
                'wagtail.core.jinja2tags.core',
                'wagtail.admin.jinja2tags.userbar',
                'wagtail.images.jinja2tags.images',
                'wagtail.contrib.settings.jinja2tags.settings',
            ],
        },
    },
]

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'wagtail.core.middleware.SiteMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
)

INSTALLED_APPS = (
    # Install wagtailredirects with its appconfig
    # Theres nothing special about wagtailredirects, we just need to have one
    # app which uses AppConfigs to test that hooks load properly
    'wagtail.contrib.redirects.apps.WagtailRedirectsAppConfig',

    'wagtail.tests.testapp',
    'wagtail.tests.demosite',
    'wagtail.tests.customuser',
    'wagtail.tests.snippets',
    'wagtail.tests.routablepage',
    'wagtail.tests.search',
    'wagtail.tests.modeladmintest',
    'wagtail.contrib.styleguide',
    'wagtail.contrib.routable_page',
    'wagtail.contrib.frontend_cache',
    'wagtail.contrib.search_promotions',
    'wagtail.contrib.settings',
    'wagtail.contrib.modeladmin',
    'wagtail.contrib.table_block',
    'wagtail.contrib.forms',
    'wagtail.search',
    'wagtail.embeds',
    'wagtail.images',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.admin',
    'wagtail.api.v2',
    'wagtail.core',

    'taggit',
    'rest_framework',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
)


# Using DatabaseCache to make sure that the cache is cleared between tests.
# This prevents false-positives in some wagtail core tests where we are
# changing the 'wagtail_root_paths' key which may cause future tests to fail.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',  # don't use the intentionally slow default password hasher
)


WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.db',
    }
}

AUTH_USER_MODEL = 'customuser.CustomUser'

if os.environ.get('DATABASE_ENGINE') == 'django.db.backends.postgresql':
    INSTALLED_APPS += ('wagtail.contrib.postgres_search',)
    WAGTAILSEARCH_BACKENDS['postgresql'] = {
        'BACKEND': 'wagtail.contrib.postgres_search.backend',
        'AUTO_UPDATE': False,
    }

if 'ELASTICSEARCH_URL' in os.environ:
    if os.environ.get('ELASTICSEARCH_VERSION') == '6':
        backend = 'wagtail.search.backends.elasticsearch6'
    elif os.environ.get('ELASTICSEARCH_VERSION') == '5':
        backend = 'wagtail.search.backends.elasticsearch5'
    elif os.environ.get('ELASTICSEARCH_VERSION') == '2':
        backend = 'wagtail.search.backends.elasticsearch2'

    WAGTAILSEARCH_BACKENDS['elasticsearch'] = {
        'BACKEND': backend,
        'URLS': [os.environ['ELASTICSEARCH_URL']],
        'TIMEOUT': 10,
        'max_retries': 1,
        'AUTO_UPDATE': False,
        'INDEX_SETTINGS': {
            'settings': {
                'index': {
                    'number_of_shards': 1
                }
            }
        }
    }


WAGTAIL_SITE_NAME = "Test Site"

# Extra user field for custom user edit and create form tests. This setting
# needs to here because it is used at the module level of wagtailusers.forms
# when the module gets loaded. The decorator 'override_settings' does not work
# in this scenario.
WAGTAIL_USER_CUSTOM_FIELDS = ['country', 'attachment']

WAGTAILADMIN_RICH_TEXT_EDITORS = {
    'default': {
        'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea'
    },
    'hallo': {
        'WIDGET': 'wagtail.admin.rich_text.HalloRichTextArea'
    },
    'custom': {
        'WIDGET': 'wagtail.tests.testapp.rich_text.CustomRichTextArea'
    },
}
