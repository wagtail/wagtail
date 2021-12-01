from django.db import transaction

from wagtail.core.utils import find_available_slug


class ParentNotTranslatedError(Exception):
    """
    Raised when a call to Page.copy_for_translation is made but the
    parent page is not translated and copy_parents is False.
    """

    pass


@transaction.atomic
def copy_for_translation(
    page, locale, copy_parents=False, alias=False, exclude_fields=None
):
    """
    Creates a copy of this page in the specified locale.

    The new page will be created in draft as a child of this page's translated
    parent.

    For example, if you are translating a blog post from English into French,
    this method will look for the French version of the blog index and create
    the French translation of the blog post under that.

    If this page's parent is not translated into the locale, then a ``ParentNotTranslatedError``
    is raised. You can circumvent this error by passing ``copy_parents=True`` which
    copies any parents that are not translated yet.

    The ``exclude_fields`` parameter can be used to set any fields to a blank value
    in the copy.

    Note that this method calls the ``.copy()`` method internally so any fields that
    are excluded in ``.exclude_fields_in_copy`` will be excluded from the translation.
    """
    # Find the translated version of the parent page to create the new page under
    parent = page.get_parent().specific
    slug = page.slug

    if not parent.is_root():
        try:
            translated_parent = parent.get_translation(locale)
        except parent.__class__.DoesNotExist:
            if not copy_parents:
                raise ParentNotTranslatedError

            translated_parent = parent.copy_for_translation(
                locale, copy_parents=True, alias=True
            )
    else:
        # Don't duplicate the root page for translation. Create new locale as a sibling
        translated_parent = parent

        # Append language code to slug as the new page
        # will be created in the same section as the existing one
        slug += "-" + locale.language_code

    # Find available slug for new page
    slug = find_available_slug(translated_parent, slug)

    if alias:
        return page.create_alias(
            parent=translated_parent,
            update_slug=slug,
            update_locale=locale,
            reset_translation_key=False,
        )

    else:
        # Update locale on translatable child objects as well
        def process_child_object(
            original_page, page_copy, child_relation, child_object
        ):
            from wagtail.core.models import TranslatableMixin

            if isinstance(child_object, TranslatableMixin):
                child_object.locale = locale

        return page.copy(
            to=translated_parent,
            update_attrs={
                "locale": locale,
                "slug": slug,
            },
            copy_revisions=False,
            keep_live=False,
            reset_translation_key=False,
            process_child_object=process_child_object,
            exclude_fields=exclude_fields,
            log_action="wagtail.copy_for_translation",
        )
