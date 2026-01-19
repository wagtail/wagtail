from django.conf import settings
from django.db.models import Model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from wagtail import hooks
from wagtail.models import Locale, Page


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
                page.copy_for_translation(locale, copy_parents=True, alias=True)


@receiver(post_save, sender=Page)
def create_translation_aliases_on_page_creation(sender, instance, created, **kwargs):
    """Signal to create aliases for programmatic page creations."""
    if not isinstance(instance, Page):
        return

    print(f"[simple_translation] signal received: created={created}, page_id={getattr(instance, 'id', None)}, translation_key={getattr(instance, 'translation_key', None)}, locale={getattr(instance, 'locale_id', None)}")

    if created and instance.translation_key:
        if instance.depth == 2:
            return

        from django.db.models.signals import post_save

        post_save.disconnect(create_translation_aliases_on_page_creation)

        try:
            for locale in Locale.objects.exclude(id=instance.locale_id):
                if not Page.objects.filter(translation_key=instance.translation_key, locale=locale).exists():
                    print(f"[simple_translation] creating alias for page {instance} in locale {locale}")
                    instance.copy_for_translation(locale, copy_parents=True, alias=True)
        finally:
            post_save.connect(create_translation_aliases_on_page_creation)
