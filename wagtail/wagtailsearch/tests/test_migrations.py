from __future__ import absolute_import, unicode_literals

import unittest

from django.db import connection
from django.test import TestCase, TransactionTestCase


@unittest.skipIf(connection.vendor != 'postgresql', 'This testcase needs PostgreSQL.')
class MigrationTransactionTestCase(TransactionTestCase):

    def test_migration_remove_editor(self):
        pass


class MigrationTestCase(TestCase):

    def test_migration_remove_editor(self):
        pass
