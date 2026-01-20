from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
import logging

from wagtail import hooks
from wagtail.models import Locale, Page

logger = logging.getLogger(__name__)


class SimpleTranslation(Model):
    """
    SimpleTranslation, dummy model to create the `submit_translation` permission.

    We need this model to be concrete or the following management commands will misbehave:
    - `remove_stale_contenttypes`, will drop the perm
    - `dump_data`, will complain about the missing table
    """

    class Meta:
        default_permissions = []
        permissions = [
            ("submit_translation", _("Can submit translations")),
        ]


@hooks.register("after_create_page")
def after_create_page(request, page):
    """Creates page aliases in other locales when a page is created.

    Whenever a page is created under a specific locale, this signal handler
    creates an alias page for that page under the other locales.

    e.g. When an editor creates the page "blog/my-blog-post" under the English
    tree, this signal handler creates an alias of that page called
    "blog/my-blog-post" under the other locales' trees.
    """
    if page.alias_of is None and getattr(settings, "WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE", False):
        # Check if the source tree needs to be synchronised into any other trees
        # Create aliases in all those locales
        for locale in Locale.objects.exclude(pk=page.locale_id):
            if not page.has_translation(locale):
                translated_page = page.copy_for_translation(locale, copy_parents=True, alias=True)
                translated_page.save(clean=False)


@receiver(post_save)
def create_translation_aliases_on_page_creation(sender, instance, created, **kwargs):
    """Signal to create aliases for programmatic page creations."""
    if not isinstance(instance, Page):
        return

    logger.debug(
        "[simple_translation] signal received: created=%s, page_id=%s, translation_key=%s, locale=%s",
        created,
        getattr(instance, "id", None),
        getattr(instance, "translation_key", None),
        getattr(instance, "locale_id", None),
    )

    if created and instance.translation_key:
        # Skip when tree sync is disabled — avoids creating aliases when the sync feature is off and prevents surprising side effects
        if not getattr(settings, "WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE", False):
            return

        # Skip raw fixture/deserialization saves — prevents test/fixture fragility during loaddata/deserialization
        if kwargs.get("raw", False):
            return

        # Skip root/homepage (depth <= 2) — avoid automatically aliasing top-level structural pages
        if instance.depth <= 2:
            return

        from django.db.models.signals import post_save

        post_save.disconnect(create_translation_aliases_on_page_creation)

        try:
            locales = list(Locale.objects.exclude(id=instance.locale_id))
            logger.debug("[simple_translation] target locales: %s", locales)
            for locale in locales:
                exists = Page.objects.filter(translation_key=instance.translation_key, locale=locale).exists()
                logger.debug(
                    "[simple_translation] checking locale %s: exists=%s",
                    locale,
                    exists,
                )
                if not exists:
                    try:
                        # Require parent to be translated; don't auto-create translated parents as that would change tree structure
                        parent = instance.get_parent().specific
                        try:
                            parent_translation = parent.get_translation(locale)
                        except parent.__class__.DoesNotExist:
                            logger.debug(
                                "[simple_translation] skipping alias creation for %s in %s because parent is not translated",
                                instance,
                                locale,
                            )
                            continue

                        logger.debug(
                            "[simple_translation] creating alias for page %s in locale %s",
                            instance,
                            locale,
                        )
                        # Don't auto-create untranslated parents here (we already ensured translated parent exists)
                        translated_page = instance.copy_for_translation(locale, copy_parents=False, alias=True)
                        translated_page.save(clean=False)
                        logger.debug(
                            "[simple_translation] created alias: %s (id=%s)",
                            translated_page,
                            getattr(translated_page, "id", None),
                        )
                    except Exception:
                        # Log exception with traceback for debugging, but don't raise
                        logger.exception(
                            "[simple_translation] failed to create alias for %s in %s",
                            instance,
                            locale,
                        )
        finally:
            post_save.connect(create_translation_aliases_on_page_creation)
