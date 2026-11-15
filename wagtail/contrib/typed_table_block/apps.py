from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _


class WagtailTypedTableBlockAppConfig(AppConfig):
    name = "wagtail.contrib.typed_table_block"
    label = "typed_table_block"
    verbose_name = _("Wagtail typed table block")

    def ready(self):
        if apps.is_installed("wagtail.api.v3"):
            from wagtail.api.v3.schemas.generators import read, write

            from .api.v3.schemas import typed_table_block_schema
            from .blocks import BaseTypedTableBlock

            for builder in (read.block_schema_builder, write.block_schema_builder):
                builder.register_block_schema(
                    BaseTypedTableBlock, typed_table_block_schema
                )
