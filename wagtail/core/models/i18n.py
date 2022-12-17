from warnings import warn

from wagtail.models.i18n import (  # noqa
    BootstrapTranslatableMixin,
    BootstrapTranslatableModel,
    Locale,
    LocaleManager,
    TranslatableMixin,
    bootstrap_translatable_model,
    get_translatable_models,
)
from wagtail.utils.deprecation import RemovedInWagtail50Warning

warn(
    "Importing from wagtail.core.models.i18n is deprecated. "
    "Use wagtail.models.i18n instead. "
    "See https://docs.wagtail.org/en/stable/releases/3.0.html#changes-to-module-paths",
    category=RemovedInWagtail50Warning,
    stacklevel=2,
)
