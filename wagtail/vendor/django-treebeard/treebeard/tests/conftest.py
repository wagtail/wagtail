import os
import sys
import time


os.environ['DJANGO_SETTINGS_MODULE'] = 'treebeard.tests.settings'

import django
from django.conf import settings
from django.test.utils import (setup_test_environment,
                               teardown_test_environment)
from django.test.client import Client
from django.core.management import call_command
from django.core import mail
from django.db import connection
from django.db.models.base import ModelBase
from _pytest import python as _pytest_python


def idmaker(argnames, argvalues):
    idlist = []
    for valindex, valset in enumerate(argvalues):
        this_id = []
        for nameindex, val in enumerate(valset):
            argname = argnames[nameindex]
            if isinstance(val, (float, int, str)):
                this_id.append(str(val))
            elif isinstance(val, ModelBase):
                this_id.append(val.__name__)
            else:
                this_id.append("{0}-{1}={2!s}".format(argname, valindex))
        idlist.append("][".join(this_id))
    return idlist
_pytest_python.idmaker = idmaker


def pytest_report_header(config):
    return 'Django: ' + django.get_version()


def pytest_configure(config):
    setup_test_environment()
    connection.creation.create_test_db(verbosity=2, autoclobber=True)


def pytest_unconfigure(config):
    dbsettings = settings.DATABASES['default']
    dbtestname = dbsettings['TEST_NAME']
    connection.close()
    if dbsettings['ENGINE'].split('.')[-1] == 'postgresql_psycopg2':
        connection.connection = None
        connection.settings_dict['NAME'] = dbtestname.split('_')[1]
        cursor = connection.cursor()
        connection.autocommit = True
        if django.VERSION < (1, 6):
            connection._set_isolation_level(0)
        else:
            connection._set_autocommit(True)
        time.sleep(1)
        sys.stdout.write(
            "Destroying test database for alias '%s' (%s)...\n" % (
                connection.alias, dbtestname)
        )
        sys.stdout.flush()
        cursor.execute(
            'DROP DATABASE %s' % connection.ops.quote_name(dbtestname))
    else:
        connection.creation.destroy_test_db(dbtestname, verbosity=2)
    teardown_test_environment()


def pytest_funcarg__client(request):
    def setup():
        mail.outbox = []
        return Client()

    def teardown(client):
        call_command('flush', verbosity=0, interactive=False)

    return request.cached_setup(setup, teardown, 'function')
