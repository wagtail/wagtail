from wagtail.core.models import UserPagePermissionsProxy
from wagtail.core.utils import find_available_slug


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
    def __init__(self, user, page, destination, recursive=False, keep_live=True, alias=False, slug=None, title=None):
        self.user = user
        self.page = page
        self.destination = destination
        self.recursive = recursive
        self.keep_live = keep_live
        self.alias = alias
        self.slug = slug
        self.title = title

    def check(self):
        # reject the logically impossible cases first
        # keep_live=False can't be used on alias pages
        if self.alias and not self.keep_live:
            raise AliasPagesMustBeKeptLive

        # recursive can't copy to the same tree otherwise it will be on infinite loop
        if self.recursive and (self.page == self.destination or self.destination.is_descendant_of(self.page)):
            raise CannotRecursivelyCopyIntoSelf

        # reject inactive users early
        if not self.user.is_active:
            raise UserCannotCreateAtDestination

        # reject early if pages of this type cannot be created at the destination
        if not self.page.specific_class.can_create_at(self.destination):
            raise PageTypeCannotBeCreatedAtDestination

        # reject if a slug was requested that already exists
        if self.slug:
            if self.destination.get_children().filter(slug=self.slug).exists():
                raise SlugInUse

        # skip permission checking for super users
        if self.user.is_superuser:
            return

        # Inspect permissions on the destination
        destination_perms = UserPagePermissionsProxy(self.user).for_page(self.destination)

        if not self.destination.specific_class.creatable_subpage_models():
            raise PageTypeCannotBeCreatedAtDestination

        # we always need at least add permission in the target
        if 'add' not in destination_perms.permissions:
            raise UserCannotCreateAtDestination

        # If the user is attempting to publish, check that permission as well
        # Note that only users who can publish in the new parent page can create an alias.
        # This is because alias pages must always match their original page's state.
        if self.alias or self.keep_live:
            if not destination_perms.can_publish_subpage():
                raise UserCannotPublishAtDestination

    def execute(self, skip_check=False):
        # Check
        if not skip_check:
            self.check()

        # If a slug wasn't explicity requested, find a slug based on the source page
        if self.slug is not None:
            slug = self.slug
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
            update_attrs = {}
            if self.title is not None:
                update_attrs['title'] = self.title
            if slug != self.page.slug:
                update_attrs['slug'] = slug

            return self.page.specific.copy(
                recursive=self.recursive,
                to=self.destination,
                update_attrs=update_attrs,
                keep_live=self.keep_live,
                user=self.user,
            )
