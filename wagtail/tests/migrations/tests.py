import os

from django.apps import apps
from django.core.management import call_command
from freezegun import freeze_time

from .test_base import MigrationTestBase

current_dir = os.path.dirname(__file__)


@freeze_time("2018-08-15 00:00")
class MakeMigrationsTests(MigrationTestBase):
    """
    Tests running the makemigrations command.
    """

    maxDiff = None

    available_apps = [
        "wagtail.tests.migrations",  # Here are the fake migrations
        "wagtail.core",  # This is where the command override lives
        # The rest are dependencies
        "wagtail.tests.customuser",
        "django.contrib.auth",
        "django.contrib.contenttypes",
    ]

    def setUp(self):
        super().setUp()
        self._old_models = apps.app_configs["migrations"].models.copy()

    def tearDown(self):
        apps.app_configs["migrations"].models = self._old_models
        apps.all_models["migrations"] = self._old_models
        apps.clear_cache()
        super().tearDown()

    def test_class_created(self):
        """
        Calling makemigrations should create a modified django migration, where
        for every StreamField modification a subclass of AlterStreamField is
        inserted
        """
        from .models import StreamModel
        apps.register_model("migrations", StreamModel)
        with self.temporary_migration_module(
            module="wagtail.tests.migrations.test_block_changed"
        ) as migration_dir:
            call_command("makemigrations", "migrations", verbosity=0)

            # Check for 0002 file in migration folder
            django_file = os.path.join(migration_dir, "0002_auto_20180815_0000.py")
            self.assertTrue(os.path.exists(django_file))
            expected_django_file = os.path.join(
                current_dir, "expected_block_changed", "0002_auto_20180815_0000.py"
            )
            with open(django_file, "r") as real:
                with open(expected_django_file, "r") as expected:
                    self.assertListEqual(real.readlines()[1:], expected.readlines()[1:])

    def test_non_streamfield_modification(self):
        """
        Non-streamfield modifications should not be affected
        """
        from .models_non_streamfield import StreamModel
        apps.register_model("migrations", StreamModel)
        with self.temporary_migration_module(
            module="wagtail.tests.migrations.test_block_changed"
        ) as migration_dir:
            call_command("makemigrations", "migrations", verbosity=0)

            # Check for 0002 file in migration folder
            django_file = os.path.join(migration_dir, "0002_streammodel_title.py")
            self.assertTrue(os.path.exists(django_file))
            expected_django_file = os.path.join(
                current_dir, "expected_non_streamfield", "0002_streammodel_title.py"
            )
            with open(django_file, "r") as real:
                with open(expected_django_file, "r") as expected:
                    self.assertListEqual(real.readlines()[1:], expected.readlines()[1:])
