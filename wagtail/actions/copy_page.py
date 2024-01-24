import logging
import uuid

from django.core.exceptions import PermissionDenied
from modelcluster.models import get_all_child_relations

from wagtail.log_actions import log
from wagtail.models.copying import _copy, _copy_m2m_relations
from wagtail.models.i18n import TranslatableMixin
from wagtail.signals import page_published

logger = logging.getLogger("wagtail")


class CopyPageIntegrityError(RuntimeError):
    """
    Raised when the page copy cannot be performed for data integrity reasons.
    """

    pass


class CopyPagePermissionError(PermissionDenied):
    """
    Raised when the page copy cannot be performed due to insufficient permissions.
    """

    pass


class CopyPageAction:
    """
    Copies pages and page trees.
    """

    def __init__(
        self,
        page,
        to=None,
        update_attrs=None,
        exclude_fields=None,
        recursive=False,
        copy_revisions=True,
        keep_live=True,
        user=None,
        process_child_object=None,
        log_action="wagtail.copy",
        reset_translation_key=True,
    ):
        # Note: These four parameters don't apply to any copied children
        self.page = page
        self.to = to
        self.update_attrs = update_attrs
        self.exclude_fields = exclude_fields

        self.recursive = recursive
        self.copy_revisions = copy_revisions
        self.keep_live = keep_live
        self.user = user
        self.process_child_object = process_child_object
        self.log_action = log_action
        self.reset_translation_key = reset_translation_key
        self._uuid_mapping = {}

    def generate_translation_key(self, old_uuid):
        """
        Generates a new UUID if it isn't already being used.
        Otherwise it will return the same UUID if it's already in use.
        """
        if old_uuid not in self._uuid_mapping:
            self._uuid_mapping[old_uuid] = uuid.uuid4()

        return self._uuid_mapping[old_uuid]

    def check(self, skip_permission_checks=False):
        # Essential data model checks
        if self.page._state.adding:
            raise CopyPageIntegrityError("Page.copy() called on an unsaved page")

        if (
            self.to
            and self.recursive
            and (self.to.id == self.page.id or self.to.is_descendant_of(self.page))
        ):
            raise CopyPageIntegrityError(
                "You cannot copy a tree branch recursively into itself"
            )

        # Permission checks
        if self.user and not skip_permission_checks:
            to = self.to
            if to is None:
                to = self.page.get_parent()

            if not self.page.permissions_for_user(self.user).can_copy_to(
                to, self.recursive
            ):
                raise CopyPagePermissionError(
                    "You do not have permission to copy this page"
                )

            if self.keep_live:
                destination_perms = self.to.permissions_for_user(self.user)

                if not destination_perms.can_publish_subpage():
                    raise CopyPagePermissionError(
                        "You do not have permission to publish a page at the destination"
                    )

    def _copy_page(
        self, page, to=None, update_attrs=None, exclude_fields=None, _mpnode_attrs=None
    ):
        specific_page = page.specific
        exclude_fields = (
            specific_page.default_exclude_fields_in_copy
            + specific_page.exclude_fields_in_copy
            + (exclude_fields or [])
        )
        if self.keep_live:
            base_update_attrs = {
                "alias_of": None,
            }
        else:
            base_update_attrs = {
                "live": False,
                "has_unpublished_changes": True,
                "live_revision": None,
                "first_published_at": None,
                "last_published_at": None,
                "alias_of": None,
            }

        if self.user:
            base_update_attrs["owner"] = self.user

        # When we're not copying for translation, we should give the translation_key a new value
        if self.reset_translation_key:
            base_update_attrs["translation_key"] = uuid.uuid4()

        if update_attrs:
            base_update_attrs.update(update_attrs)

        page_copy, child_object_map = _copy(
            specific_page, exclude_fields=exclude_fields, update_attrs=base_update_attrs
        )
        # Save copied child objects and run process_child_object on them if we need to
        for (child_relation, old_pk), child_object in child_object_map.items():
            if self.process_child_object:
                self.process_child_object(
                    specific_page, page_copy, child_relation, child_object
                )

            if self.reset_translation_key and isinstance(
                child_object, TranslatableMixin
            ):
                child_object.translation_key = self.generate_translation_key(
                    child_object.translation_key
                )

        # Save the new page
        if _mpnode_attrs:
            # We've got a tree position already reserved. Perform a quick save
            page_copy.path = _mpnode_attrs[0]
            page_copy.depth = _mpnode_attrs[1]
            page_copy.save(clean=False)

        else:
            if to:
                page_copy = to.add_child(instance=page_copy)
            else:
                page_copy = page.add_sibling(instance=page_copy)

            _mpnode_attrs = (page_copy.path, page_copy.depth)

        _copy_m2m_relations(
            specific_page,
            page_copy,
            exclude_fields=exclude_fields,
            update_attrs=base_update_attrs,
        )

        # Copy revisions
        if self.copy_revisions:
            for revision in page.revisions.all():
                use_as_latest_revision = revision.pk == page.latest_revision_id
                revision.pk = None
                revision.approved_go_live_at = None
                revision.object_id = page_copy.id

                # Update ID fields in content
                revision_content = revision.content
                revision_content["pk"] = page_copy.pk

                for child_relation in get_all_child_relations(specific_page):
                    accessor_name = child_relation.get_accessor_name()
                    try:
                        child_objects = revision_content[accessor_name]
                    except KeyError:
                        # KeyErrors are possible if the revision was created
                        # before this child relation was added to the database
                        continue

                    for child_object in child_objects:
                        child_object[child_relation.field.name] = page_copy.pk
                        # Remap primary key to copied versions
                        # If the primary key is not recognised (eg, the child object has been deleted from the database)
                        # set the primary key to None
                        copied_child_object = child_object_map.get(
                            (child_relation, child_object["pk"])
                        )
                        child_object["pk"] = (
                            copied_child_object.pk if copied_child_object else None
                        )
                        if (
                            self.reset_translation_key
                            and "translation_key" in child_object
                        ):
                            child_object[
                                "translation_key"
                            ] = self.generate_translation_key(
                                child_object["translation_key"]
                            )

                for exclude_field in specific_page.exclude_fields_in_copy:
                    if exclude_field in revision_content and hasattr(
                        page_copy, exclude_field
                    ):
                        revision_content[exclude_field] = getattr(
                            page_copy, exclude_field, None
                        )

                revision.content = revision_content

                # Save
                revision.save()
                # If this revision was designated the latest revision, update the page copy to point to the copied revision
                if use_as_latest_revision:
                    page_copy.latest_revision = revision

        # Create a new revision
        # This code serves a few purposes:
        # * It makes sure update_attrs gets applied to the latest revision
        # * It bumps the last_revision_created_at value so the new page gets ordered as if it was just created
        # * It sets the user of the new revision so it's possible to see who copied the page by looking at its history
        latest_revision = page_copy.get_latest_revision_as_object()

        if update_attrs:
            for field, value in update_attrs.items():
                setattr(latest_revision, field, value)

        latest_revision_as_page_revision = latest_revision.save_revision(
            user=self.user, changed=False, clean=False
        )

        # save_revision should have updated this in the database - update the in-memory copy for consistency
        page_copy.latest_revision = latest_revision_as_page_revision

        if self.keep_live:
            page_copy.live_revision = latest_revision_as_page_revision
            page_copy.last_published_at = latest_revision_as_page_revision.created_at
            page_copy.first_published_at = latest_revision_as_page_revision.created_at
            # The call to save_revision above will have updated several fields of the page record, including
            # draft_title and latest_revision. These changes are not reflected in page_copy, so we must only
            # update the specific fields set above to avoid overwriting them.
            page_copy.save(
                clean=False,
                update_fields=[
                    "live_revision",
                    "last_published_at",
                    "first_published_at",
                ],
            )

        if page_copy.live:
            page_published.send(
                sender=page_copy.specific_class,
                instance=page_copy,
                revision=latest_revision_as_page_revision,
            )

        # Log
        if self.log_action:
            parent = specific_page.get_parent()
            log(
                instance=page_copy,
                action=self.log_action,
                user=self.user,
                data={
                    "page": {
                        "id": page_copy.id,
                        "title": page_copy.get_admin_display_title(),
                        "locale": {
                            "id": page_copy.locale_id,
                            "language_code": page_copy.locale.language_code,
                        },
                    },
                    "source": {
                        "id": parent.id,
                        "title": parent.specific_deferred.get_admin_display_title(),
                    }
                    if parent
                    else None,
                    "destination": {
                        "id": to.id,
                        "title": to.specific_deferred.get_admin_display_title(),
                    }
                    if to
                    else None,
                    "keep_live": page_copy.live and self.keep_live,
                    "source_locale": {
                        "id": page.locale_id,
                        "language_code": page.locale.language_code,
                    },
                },
            )
            if page_copy.live and self.keep_live:
                # Log the publish if the use chose to keep the copied page live
                log(
                    instance=page_copy,
                    action="wagtail.publish",
                    user=self.user,
                    revision=latest_revision_as_page_revision,
                )
        logger.info(
            'Page copied: "%s" id=%d from=%d', page_copy.title, page_copy.id, page.id
        )

        # Copy child pages
        from wagtail.models import Page, PageViewRestriction

        if self.recursive:
            numchild = 0

            for child_page in page.get_children().specific().iterator():
                newdepth = _mpnode_attrs[1] + 1
                child_mpnode_attrs = (
                    Page._get_path(_mpnode_attrs[0], newdepth, numchild),
                    newdepth,
                )
                numchild += 1
                self._copy_page(
                    child_page, to=page_copy, _mpnode_attrs=child_mpnode_attrs
                )

            if numchild > 0:
                page_copy.numchild = numchild
                page_copy.save(clean=False, update_fields=["numchild"])

        # Copy across any view restrictions defined directly on the page,
        # unless the destination page already has view restrictions defined
        if to:
            parent_page_restriction = to.get_view_restrictions()
        else:
            parent_page_restriction = self.page.get_parent().get_view_restrictions()

        if not parent_page_restriction.exists():
            for view_restriction in self.page.view_restrictions.all():
                view_restriction_copy = PageViewRestriction(
                    restriction_type=view_restriction.restriction_type,
                    password=view_restriction.password,
                    page=page_copy,
                )
                view_restriction_copy.save(user=self.user)
                view_restriction_copy.groups.set(view_restriction.groups.all())

        return page_copy

    def execute(self, skip_permission_checks=False):
        self.check(skip_permission_checks=skip_permission_checks)

        return self._copy_page(
            self.page,
            to=self.to,
            update_attrs=self.update_attrs,
            exclude_fields=self.exclude_fields,
        )
