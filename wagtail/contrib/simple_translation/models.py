from django.conf import settings
from django.db.models import Model

from wagtail import hooks
from wagtail.models import Locale


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
            ("submit_translation", "Can submit translations"),
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
    if getattr(settings, "WAGTAILSIMPLETRANSLATION_SYNC_PAGE_TREE", False):
        # Check if the source tree needs to be synchronised into any other trees
        # Create aliases in all those locales
        for locale in Locale.objects.exclude(pk=page.locale_id):
            if not page.has_translation(locale):
                page.copy_for_translation(locale, copy_parents=True, alias=True)
