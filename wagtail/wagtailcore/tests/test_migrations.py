"""
Check that all changes to Wagtail models have had migrations created. If there
are outstanding model changes that need migrations, fail the tests.
"""

from django import VERSION
from django.test import TransactionTestCase

from django.utils.six import iteritems
import south.management.commands.schemamigration

try:
    from unittest import skipIf, skipUnless
except ImportError:
    from django.utils.unittest import skipIf, skipUnless


class TestForMigrations(TransactionTestCase):

    @skipIf(VERSION < (1, 7), "Migrations introduced in Django 1.7")
    def test_django_17_migrations(self):

        from django.apps import apps
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.autodetector import MigrationAutodetector
        from django.db.migrations.state import ProjectState
        from django.db.migrations.questioner import MigrationQuestioner
        app_labels = set(app.label for app in apps.get_app_configs()
                         if app.name.startswith('wagtail.'))
        for app_label in app_labels:
            apps.get_app_config(app_label.split('.')[-1])
        loader = MigrationLoader(None, ignore_no_migrations=True)

        conflicts = dict(
            (app_label, conflict)
            for app_label, conflict in iteritems(loader.detect_conflicts())
            if app_label in app_labels
        )

        if conflicts:
            name_str = "; ".join("%s in %s" % (", ".join(names), app)
                                 for app, names in conflicts.items())
            self.fail("Conflicting migrations detected (%s)." % name_str)

        autodetector = MigrationAutodetector(
            loader.project_state(),
            ProjectState.from_apps(apps),
            MigrationQuestioner(specified_apps=app_labels, dry_run=True),
        )

        changes = autodetector.changes(
            graph=loader.graph,
            trim_to_apps=app_labels or None,
            convert_apps=app_labels or None,
        )

        if changes:
            apps = ', '.join(apps.get_app_config(label).name
                             for label in changes.keys())
            self.fail('Model changes with no migrations detected in apps: %s' % (apps,))

    @skipUnless(VERSION < (1, 7), "South migrations used for Django < 1.7")
    def test_south_migrations(self):

        from django.core.exceptions import ImproperlyConfigured
        from django.conf import settings
        from django.db import models

        from south.migration import Migrations, migrate_app
        from south.models import MigrationHistory
        from south.exceptions import NoMigrations
        from south.creator import changes, actions, freezer
        from south.management.commands.datamigration import Command as DataCommand

        apps = [app for app in settings.INSTALLED_APPS
                if app.startswith('wagtail.')]
        failing_apps = []
        for app_name in apps:
            app = app_name.split('.')[-1]
            try:
                models.get_app(app)
            except ImproperlyConfigured:
                # This module fails to load, probably because it has no
                # models.py. Ignore it and move on
                continue

            try:
                migrations = Migrations(app, force_creation=False, verbose_creation=False)
                last_migration = migrations[-1]
            except (NoMigrations, IndexError):
                # No migrations for this app, probably doesnt have models
                continue

            if migrations.app_label() not in getattr(last_migration.migration_class(), "complete_apps", []):
                self.fail("Automatic migrations checking failed, since the previous migration does not have this whole app frozen.\nEither make migrations using '--freeze %s' or set 'SOUTH_AUTO_FREEZE_APP = True' in your settings.py." % migrations.app_label())

            # Alright, construct two model dicts to run the differ on.
            old_defs = dict(
                (k, v) for k, v in last_migration.migration_class().models.items()
                if k.split(".")[0] == migrations.app_label()
            )
            new_defs = dict(
                (k, v) for k, v in freezer.freeze_apps([migrations.app_label()]).items()
                if k.split(".")[0] == migrations.app_label()
            )
            change_source = changes.AutoChanges(
                migrations = migrations,
                old_defs = old_defs,
                old_orm = last_migration.orm(),
                new_defs = new_defs,
            )

            name = 'test'

            # Get the actions, and then insert them into the actions lists
            if list(change_source.get_changes()):
                failing_apps.append(app_name)

        if failing_apps:
            self.fail('Model changes with no South migration detected in apps: %s' % (
                ', '.join(failing_apps)))
