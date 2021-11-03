import json
import uuid
import logging

from modelcluster.models import get_all_child_relations

from wagtail.core.log_actions import log
from wagtail.core.models import Page, UserPagePermissionsProxy
from wagtail.core.models.copying import _copy, _copy_m2m_relations
from wagtail.core.models.i18n import TranslatableMixin
from wagtail.core.signals import page_published
from wagtail.core.utils import find_available_slug


logger = logging.getLogger('wagtail.core')


class PageCopyError(Exception):
    pass


class CannotRecursivelyCopyIntoSelf(PageCopyError):
    """
    A page cannot be recursively copied into itself or an infinite recursion will occur.
    """
    pass


class UserCannotCreateAtDestination(PageCopyError):
    """
    The user does not have permission to create pages in the destination.
    """
    pass


class UserCannotPublishAtDestination(PageCopyError):
    """
    The user does not have permission to publish pages in the destination.

    This is required for creating aliases or 'keep_live'
    """
    pass


class PageTypeCannotBeCreatedAtDestination(PageCopyError):
    """
    The page type cannot be created under the destination page due to page type constraints (subpage_types, parent_page_types)
    """
    pass


class SlugInUse(PageCopyError):
    """
    Can't use the specified slug because there is already a page using that slug in the destination
    """
    pass


class AliasPagesMustBeKeptLive(PageCopyError):
    """
    Can't use alias=True with keep_live=False because the alias must always have the same status as the source page.
    """
    pass


class CopyPageAction:
    def __init__(self, user, page, destination, recursive=False, keep_live=True, alias=False, copy_revisions=True, reset_translation_key=False, slug=None, title=None, process_child_object=None, log_action='wagtail.copy'):
        self.user = user
        self.page = page
        self.destination = destination
        self.recursive = recursive
        self.keep_live = keep_live
        self.alias = alias
        self.copy_revisions = copy_revisions
        self.reset_translation_key = reset_translation_key
        self.slug = slug
        self.title = title
        self.process_child_object = process_child_object
        self.log_action = log_action

        if page._state.adding:
            raise RuntimeError('unsaved page passed in to CopyPageAction')

        if self.destination is None:
            self.destination = page.get_parent()

    def check(self):
        # reject the logically impossible cases first
        # keep_live=False can't be used on alias pages
        if self.alias and not self.keep_live:
            raise AliasPagesMustBeKeptLive

        # recursive can't copy to the same tree otherwise it will be on infinite loop
        if self.recursive and (self.page.id == self.destination.id or self.destination.is_descendant_of(self.page)):
            raise CannotRecursivelyCopyIntoSelf

        # reject inactive users early
        if self.user and not self.user.is_active:
            raise UserCannotCreateAtDestination

        # reject early if pages of this type cannot be created at the destination
        if not self.page.specific_class.can_create_at(self.destination):
            raise PageTypeCannotBeCreatedAtDestination

        # reject if a slug was requested that already exists
        if self.slug:
            if self.destination.get_children().filter(slug=self.slug).exists():
                raise SlugInUse

        # skip permission checking for super users
        if self.user and self.user.is_superuser:
            return

        if not self.destination.specific_class.creatable_subpage_models():
            raise PageTypeCannotBeCreatedAtDestination

        # Inspect user permissions on the destination
        if self.user:
            destination_perms = UserPagePermissionsProxy(self.user).for_page(self.destination)

            # we always need at least add permission in the target
            if 'add' not in destination_perms.permissions:
                raise UserCannotCreateAtDestination

            # If the user is attempting to publish, check that permission as well
            # Note that only users who can publish in the new parent page can create an alias.
            # This is because alias pages must always match their original page's state.
            if self.alias or self.keep_live:
                if not destination_perms.can_publish_subpage():
                    raise UserCannotPublishAtDestination

    def copy_page(self, page, destination, update_attrs=None, exclude_fields=None, _mpnode_attrs=None):
        exclude_fields = page.default_exclude_fields_in_copy + page.exclude_fields_in_copy + (exclude_fields or [])
        specific_page = page.specific
        if self.keep_live:
            base_update_attrs = {
                'alias_of': None,
            }
        else:
            base_update_attrs = {
                'live': False,
                'has_unpublished_changes': True,
                'live_revision': None,
                'first_published_at': None,
                'last_published_at': None,
                'alias_of': None,
            }

        if self.user:
            base_update_attrs['owner'] = self.user

        # When we're not copying for translation, we should give the translation_key a new value
        if self.reset_translation_key:
            base_update_attrs['translation_key'] = uuid.uuid4()

        if update_attrs:
            base_update_attrs.update(update_attrs)

        page_copy, child_object_map = _copy(specific_page, exclude_fields=exclude_fields, update_attrs=base_update_attrs)

        # Save copied child objects and run process_child_object on them if we need to
        for (child_relation, old_pk), child_object in child_object_map.items():
            if self.process_child_object:
                self.process_child_object(specific_page, page_copy, child_relation, child_object)

            # When we're not copying for translation, we should give the translation_key a new value for each child object as well
            if self.reset_translation_key and isinstance(child_object, TranslatableMixin):
                child_object.translation_key = uuid.uuid4()

        # Save the new page
        if _mpnode_attrs:
            # We've got a tree position already reserved. Perform a quick save
            page_copy.path = _mpnode_attrs[0]
            page_copy.depth = _mpnode_attrs[1]
            page_copy.save(clean=False)

        else:
            if destination:
                if self.recursive and (destination == page or destination.is_descendant_of(page)):
                    raise Exception("You cannot copy a tree branch recursively into itself")
                page_copy = destination.add_child(instance=page_copy)
            else:
                page_copy = page.add_sibling(instance=page_copy)

            _mpnode_attrs = (page_copy.path, page_copy.depth)

        _copy_m2m_relations(specific_page, page_copy, exclude_fields=exclude_fields, update_attrs=base_update_attrs)

        # Copy revisions
        if self.copy_revisions:
            for revision in page.revisions.all():
                revision.pk = None
                revision.submitted_for_moderation = False
                revision.approved_go_live_at = None
                revision.page = page_copy

                # Update ID fields in content
                revision_content = json.loads(revision.content_json)
                revision_content['pk'] = page_copy.pk

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
                        copied_child_object = child_object_map.get((child_relation, child_object['pk']))
                        child_object['pk'] = copied_child_object.pk if copied_child_object else None

                revision.content_json = json.dumps(revision_content)

                # Save
                revision.save()

        # Create a new revision
        # This code serves a few purposes:
        # * It makes sure update_attrs gets applied to the latest revision
        # * It bumps the last_revision_created_at value so the new page gets ordered as if it was just created
        # * It sets the user of the new revision so it's possible to see who copied the page by looking at its history
        latest_revision = page_copy.get_latest_revision_as_page()

        if update_attrs:
            for field, value in update_attrs.items():
                setattr(latest_revision, field, value)

        latest_revision_as_page_revision = latest_revision.save_revision(user=self.user, changed=False, clean=False)
        if self.keep_live:
            page_copy.live_revision = latest_revision_as_page_revision
            page_copy.last_published_at = latest_revision_as_page_revision.created_at
            page_copy.first_published_at = latest_revision_as_page_revision.created_at
            page_copy.save(clean=False)

        if page_copy.live:
            page_published.send(
                sender=page_copy.specific_class, instance=page_copy,
                revision=latest_revision_as_page_revision
            )

        # Log
        if self.log_action:
            parent = specific_page.get_parent()
            log(
                instance=page_copy,
                action=self.log_action,
                user=self.user,
                data={
                    'page': {
                        'id': page_copy.id,
                        'title': page_copy.get_admin_display_title(),
                        'locale': {
                            'id': page_copy.locale_id,
                            'language_code': page_copy.locale.language_code
                        }
                    },
                    'source': {'id': parent.id, 'title': parent.specific_deferred.get_admin_display_title()} if parent else None,
                    'destination': {'id': destination.id, 'title': destination.specific_deferred.get_admin_display_title()} if destination else None,
                    'keep_live': page_copy.live and self.keep_live,
                    'source_locale': {
                        'id': page.locale_id,
                        'language_code': page.locale.language_code
                    }
                },
            )
            if page_copy.live and self.keep_live:
                # Log the publish if the use chose to keep the copied page live
                log(
                    instance=page_copy,
                    action='wagtail.publish',
                    user=self.user,
                    revision=latest_revision_as_page_revision,
                )
        logger.info("Page copied: \"%s\" id=%d from=%d", page_copy.title, page_copy.id, page.id)

        # Copy child pages
        if self.recursive:
            numchild = 0

            for child_page in page.get_children().specific():
                newdepth = _mpnode_attrs[1] + 1
                child_mpnode_attrs = (
                    Page._get_path(_mpnode_attrs[0], newdepth, numchild),
                    newdepth
                )
                numchild += 1
                self.copy_page(
                    child_page,
                    page_copy,
                    _mpnode_attrs=child_mpnode_attrs,
                )

            if numchild > 0:
                page_copy.numchild = numchild
                page_copy.save(clean=False, update_fields=['numchild'])

        return page_copy

    def execute(self, skip_check=False, update_attrs=None, exclude_fields=None):
        # Check
        if not skip_check:
            self.check()

        # If a slug wasn't explicity requested, find a slug based on the source page
        if self.slug is not None:
            slug = self.slug
        elif update_attrs and 'slug' in update_attrs:  # FIXME
            slug = update_attrs['slug']
        else:
            slug = find_available_slug(self.destination, self.page.slug)

        # Copy the page
        if self.alias:
            return self.page.specific.create_alias(
                recursive=self.recursive,
                parent=self.destination,
                update_slug=slug,
                user=self.user,
            )
        else:
            update_attrs = update_attrs or {}
            if self.title is not None:
                update_attrs['title'] = self.title
            if slug != self.page.slug:
                update_attrs['slug'] = slug

            return self.copy_page(
                self.page,
                self.destination,
                update_attrs=update_attrs,
                exclude_fields=exclude_fields,
            )
