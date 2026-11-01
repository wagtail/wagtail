from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _


class WagtailTableBlockAppConfig(AppConfig):
    name = "wagtail.contrib.table_block"
    label = "wagtailtableblock"
    verbose_name = _("Wagtail table block")

    def ready(self):
        if apps.is_installed("wagtail.api.v3"):
            from wagtail.api.v3.schemas.generators import read, write

            from .api.v3.schemas import table_block_schema
            from .blocks import TableBlock

            for builder in (read.block_schema_builder, write.block_schema_builder):
                builder.register_block_schema(TableBlock, table_block_schema)
