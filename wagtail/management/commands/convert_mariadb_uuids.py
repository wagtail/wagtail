from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import connection, models

from wagtail.models import (
    BaseLogEntry,
    BootstrapTranslatableMixin,
    ReferenceIndex,
    TranslatableMixin,
)


class Command(BaseCommand):
    help = "Converts UUID columns from char type to the native UUID type used in MariaDB 10.7+ and Django 5.0+."

    def convert_field(self, model, field_name, null=False):
        if model._meta.get_field(field_name).model != model:
            # Field is inherited from a parent model
            return

        if not model._meta.managed:
            # The migration framework skips unmanaged models, so we should too
            return

        old_field = models.CharField(null=null, max_length=36)
        old_field.set_attributes_from_name(field_name)

        new_field = models.UUIDField(null=null)
        new_field.set_attributes_from_name(field_name)

        with connection.schema_editor() as schema_editor:
            schema_editor.alter_field(model, old_field, new_field)

    def handle(self, **options):
        self.convert_field(ReferenceIndex, "content_path_hash")

        for model in apps.get_models():
            if issubclass(model, BaseLogEntry):
                self.convert_field(model, "uuid", null=True)
            elif issubclass(model, BootstrapTranslatableMixin):
                self.convert_field(model, "translation_key", null=True)
            elif issubclass(model, TranslatableMixin):
                self.convert_field(model, "translation_key")
