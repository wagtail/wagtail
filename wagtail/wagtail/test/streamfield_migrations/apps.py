from django.apps import AppConfig


class WagtailSnippetsTestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "wagtail.test.streamfield_migrations"
    label = "streamfield_migration_tests"
    verbose_name = "Wagtail StreamField migration tests"
