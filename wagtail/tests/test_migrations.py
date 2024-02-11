"""
Check that all changes to Wagtail models have had migrations created. If there
are outstanding model changes that need migrations, fail the tests.
"""

from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.questioner import MigrationQuestioner
from django.db.migrations.state import ProjectState
from django.test import TestCase


class TestForMigrations(TestCase):
    def test__migrations(self):
        app_labels = {
            app.label
            for app in apps.get_app_configs()
            if app.name.split(".")[0] == "wagtail"
        }
        for app_label in app_labels:
            apps.get_app_config(app_label.split(".")[-1])
        loader = MigrationLoader(None, ignore_no_migrations=True)

        conflicts = {
            (app_label, conflict)
            for app_label, conflict in loader.detect_conflicts().items()
            if app_label in app_labels
        }

        if conflicts:
            name_str = "; ".join(
                "{} in {}".format(", ".join(names), app)
                for app, names in conflicts.items()
            )
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
            migrations = "\n".join(
                "  {migration}\n{changes}".format(
                    migration=migration,
                    changes="\n".join(
                        f"    {operation.describe()}"
                        for operation in migration.operations
                    ),
                )
                for (_, migrations) in changes.items()
                for migration in migrations
            )

            self.fail("Model changes with no migrations detected:\n%s" % migrations)
