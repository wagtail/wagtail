from django.apps import apps
from django.core.signals import setting_changed
from django.dispatch import receiver

# DIRECT_FORM_FIELD_OVERRIDES, FORM_FIELD_OVERRIDES are imported for backwards
# compatibility, as people are likely importing them from here and then
# appending their own overrides
from wagtail.admin.forms.models import (  # NOQA
    DIRECT_FORM_FIELD_OVERRIDES,
    FORM_FIELD_OVERRIDES,
)
from wagtail.models import Page

from .base import *  # NOQA
from .comment_panel import *  # NOQA
from .deprecated import *  # NOQA
from .field_panel import *  # NOQA
from .group import *  # NOQA
from .help_panel import *  # NOQA
from .inline_panel import *  # NOQA
from .model_utils import *  # NOQA
from .model_utils import get_edit_handler
from .page_chooser_panel import *  # NOQA
from .page_utils import *  # NOQA
from .page_utils import set_default_page_edit_handlers
from .publishing_panel import *  # NOQA


@receiver(setting_changed)
def reset_edit_handler_cache(**kwargs):
    """
    Clear page edit handler cache when global WAGTAILADMIN_COMMENTS_ENABLED settings are changed
    """
    if kwargs["setting"] == "WAGTAILADMIN_COMMENTS_ENABLED":
        set_default_page_edit_handlers(Page)
        for model in apps.get_models():
            if issubclass(model, Page):
                model.get_edit_handler.cache_clear()
        get_edit_handler.cache_clear()
