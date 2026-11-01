from django.apps import AppConfig, apps
from django.utils.translation import gettext_lazy as _

from .finders import get_finders


class WagtailEmbedsAppConfig(AppConfig):
    name = "wagtail.embeds"
    label = "wagtailembeds"
    verbose_name = _("Wagtail embeds")
    default_auto_field = "django.db.models.AutoField"

    def ready(self):
        from . import signal_handlers  # noqa

        # Check configuration on startup
        get_finders()

        if apps.is_installed("wagtail.api.v3"):
            from wagtail.api.v3.schemas.generators import read, write
            from wagtail.api.v3.schemas.generators.blocks import fixed_schema

            from .blocks import EmbedBlock

            # Its value is the embed's URL
            for builder in (read.block_schema_builder, write.block_schema_builder):
                builder.register_block_schema(EmbedBlock, fixed_schema(str | None))
