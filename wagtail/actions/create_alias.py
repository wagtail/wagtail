import logging
import uuid

from django.core.exceptions import PermissionDenied

from wagtail.log_actions import log
from wagtail.models.copying import _copy, _copy_m2m_relations
from wagtail.models.i18n import TranslatableMixin

logger = logging.getLogger("wagtail")


class CreatePageAliasIntegrityError(RuntimeError):
    """
    Raised when creating an alias of a page cannot be performed for data integrity reasons.
    """

    pass


class CreatePageAliasPermissionError(PermissionDenied):
    """
    Raised when creating an alias of a page cannot be performed due to insufficient permissions.
    """

    pass


class CreatePageAliasAction:
    """
    Creates an alias of the given page.

    An alias is like a copy, but an alias remains in sync with the original page. They
    are not directly editable and do not have revisions.

    You can convert an alias into a regular page by setting the .alias_of attribute to None
    and creating an initial revision.

    :param recursive: create aliases of the page's subtree, defaults to False
    :type recursive: boolean, optional
    :param parent: The page to create the new alias under
    :type parent: Page, optional
    :param update_slug: The slug of the new alias page, defaults to the slug of the original page
    :type update_slug: string, optional
    :param update_locale: The locale of the new alias page, defaults to the locale of the original page
    :type update_locale: Locale, optional
    :param user: The user who is performing this action. This user would be assigned as the owner of the new page and appear in the audit log
    :type user: User, optional
    :param log_action: Override the log action with a custom one. or pass None to skip logging, defaults to 'wagtail.create_alias'
    :type log_action: string or None, optional
    :param reset_translation_key: Generate new translation_keys for the page and any translatable child objects, defaults to False
    :type reset_translation_key: boolean, optional
    """

    def __init__(
        self,
        page,
        *,
        recursive=False,
        parent=None,
        update_slug=None,
        update_locale=None,
        user=None,
        log_action="wagtail.create_alias",
        reset_translation_key=True,
        _mpnode_attrs=None,
    ):
        self.page = page
        self.recursive = recursive
        self.parent = parent
        self.update_slug = update_slug
        self.update_locale = update_locale
        self.user = user
        self.log_action = log_action
        self.reset_translation_key = reset_translation_key
        self._mpnode_attrs = _mpnode_attrs

    def check(self, skip_permission_checks=False):
        parent = self.parent or self.page.get_parent()
        if self.recursive and (
            parent == self.page or parent.is_descendant_of(self.page)
        ):
            raise CreatePageAliasIntegrityError(
                "You cannot copy a tree branch recursively into itself"
            )

        if (
            self.user
            and not skip_permission_checks
            and not parent.permissions_for_user(self.user).can_publish_subpage()
        ):
            raise CreatePageAliasPermissionError(
                "You do not have permission to publish a page at the destination"
            )

    def _create_alias(
        self,
        page,
        *,
        recursive,
        parent,
        update_slug,
        update_locale,
        user,
        log_action,
        reset_translation_key,
        _mpnode_attrs,
    ):

        specific_page = page.specific

        # FIXME: Switch to the same fields that are excluded from copy
        # We can't do this right now because we can't exclude fields from with_content_json
        # which we use for updating aliases
        exclude_fields = [
            "id",
            "path",
            "depth",
            "numchild",
            "url_path",
            "path",
            "index_entries",
            "postgres_index_entries",
        ]

        update_attrs = {
            "alias_of": page,
            # Aliases don't have revisions so the draft title should always match the live title
            "draft_title": page.title,
            # Likewise, an alias page can't have unpublished changes if it's live
            "has_unpublished_changes": not page.live,
        }

        if update_slug:
            update_attrs["slug"] = update_slug

        if update_locale:
            update_attrs["locale"] = update_locale

        if user:
            update_attrs["owner"] = user

        # When we're not copying for translation, we should give the translation_key a new value
        if reset_translation_key:
            update_attrs["translation_key"] = uuid.uuid4()

        alias, child_object_map = _copy(
            specific_page, update_attrs=update_attrs, exclude_fields=exclude_fields
        )

        # Update any translatable child objects
        for child_object in child_object_map.values():
            if isinstance(child_object, TranslatableMixin):
                if update_locale:
                    child_object.locale = update_locale

                # When we're not copying for translation,
                # we should give the translation_key a new value for each child object as well.
                if reset_translation_key:
                    child_object.translation_key = uuid.uuid4()

        # Save the new page
        if _mpnode_attrs:
            # We've got a tree position already reserved. Perform a quick save.
            alias.path = _mpnode_attrs[0]
            alias.depth = _mpnode_attrs[1]
            alias.save(clean=False)

        else:
            if parent:
                alias = parent.add_child(instance=alias)
            else:
                alias = page.add_sibling(instance=alias)

            _mpnode_attrs = (alias.path, alias.depth)

        _copy_m2m_relations(specific_page, alias, exclude_fields=exclude_fields)

        # Log
        if log_action:
            source_parent = specific_page.get_parent()
            log(
                instance=alias,
                action=log_action,
                user=user,
                data={
                    "page": {"id": alias.id, "title": alias.get_admin_display_title()},
                    "source": {
                        "id": source_parent.id,
                        "title": source_parent.specific_deferred.get_admin_display_title(),
                    }
                    if source_parent
                    else None,
                    "destination": {
                        "id": parent.id,
                        "title": parent.specific_deferred.get_admin_display_title(),
                    }
                    if parent
                    else None,
                },
            )
            if alias.live:
                # Log the publish
                log(
                    instance=alias,
                    action="wagtail.publish",
                    user=user,
                )

        logger.info(
            'Page alias created: "%s" id=%d from=%d', alias.title, alias.id, page.id
        )

        # Copy child pages
        if recursive:
            from wagtail.models import Page

            numchild = 0

            for child_page in page.get_children().specific().iterator():
                newdepth = _mpnode_attrs[1] + 1
                child_mpnode_attrs = (
                    Page._get_path(_mpnode_attrs[0], newdepth, numchild),
                    newdepth,
                )
                numchild += 1
                self._create_alias(
                    child_page,
                    recursive=True,
                    parent=alias,
                    update_slug=None,
                    update_locale=update_locale,
                    user=user,
                    log_action=log_action,
                    reset_translation_key=reset_translation_key,
                    _mpnode_attrs=child_mpnode_attrs,
                )

            if numchild > 0:
                alias.numchild = numchild
                alias.save(clean=False, update_fields=["numchild"])

        return alias

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        return self._create_alias(
            self.page,
            recursive=self.recursive,
            parent=self.parent,
            update_slug=self.update_slug,
            update_locale=self.update_locale,
            user=self.user,
            log_action=self.log_action,
            reset_translation_key=self.reset_translation_key,
            _mpnode_attrs=self._mpnode_attrs,
        )
