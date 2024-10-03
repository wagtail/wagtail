from django.core.signals import setting_changed
from django.dispatch import receiver

from .finders import get_finders


@receiver(setting_changed)
def clear_embed_caches(*, setting: str, **kwargs: dict) -> None:
    """
    Clear the embed caches when settings change
    """
    if setting == "WAGTAILEMBEDS_FINDERS":
        get_finders.cache_clear()
