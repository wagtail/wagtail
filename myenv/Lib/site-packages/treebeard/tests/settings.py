"""
Django settings for testing treebeard
"""

import os


def get_db_conf():
    """
    Configures database according to the DATABASE_ENGINE environment
    variable. Defaults to SQlite.

    This method is used to run tests against different database backends.
    """
    database_engine = os.environ.get('DATABASE_ENGINE', 'sqlite')
    if database_engine == 'sqlite':
        return {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    elif database_engine == 'psql':
        return {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'treebeard',
            'USER': os.environ.get('DATABASE_USER_POSTGRES', 'treebeard'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT_POSTGRES', ''),
        }
    elif database_engine == "mysql":
        return {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'treebeard',
            'USER': os.environ.get('DATABASE_USER_MYSQL', 'treebeard'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT_MYSQL', ''),
        }
    elif database_engine == "mssql":
        return {
            'ENGINE': 'mssql',
            'NAME': 'master',
            'USER': 'sa',
            'PASSWORD': 'Password12!',
            'HOST': '(local)\\SQL2019',
            'PORT': '',
            'OPTIONS': {
                'driver': 'SQL Server Native Client 11.0',
            },
        }


DATABASES = {'default': get_db_conf()}
SECRET_KEY = '7r33b34rd'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.messages',
    'treebeard',
    'treebeard.tests'
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
]

ROOT_URLCONF = 'treebeard.tests.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
