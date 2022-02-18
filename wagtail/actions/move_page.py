import logging

from django.core.exceptions import PermissionDenied
from django.db import transaction
from treebeard.mp_tree import MP_MoveHandler

from wagtail.log_actions import log
from wagtail.signals import post_page_move, pre_page_move

logger = logging.getLogger("wagtail")


class MovePagePermissionError(PermissionDenied):
    """
    Raised when the page move cannot be performed due to insufficient permissions.
    """

    pass


class MovePageAction:
    def __init__(self, page, target, pos=None, user=None):
        self.page = page
        self.target = target
        self.pos = pos
        self.user = user

    def check(self, parent_after, skip_permission_checks=False):
        if self.user and not skip_permission_checks:
            if not self.page.permissions_for_user(self.user).can_move_to(parent_after):
                raise MovePagePermissionError(
                    "You do not have permission to move the page to the target specified."
                )

    def _move_page(self, page, target, parent_after):
        from wagtail.models import Page

        # Determine old and new url_paths
        # Fetching new object to avoid affecting `page`
        parent_before = page.get_parent()
        old_page = Page.objects.get(id=page.id)
        old_url_path = old_page.url_path
        new_url_path = old_page.set_url_path(parent=parent_after)
        url_path_changed = old_url_path != new_url_path

        # Emit pre_page_move signal
        pre_page_move.send(
            sender=page.specific_class or page.__class__,
            instance=page,
            parent_page_before=parent_before,
            parent_page_after=parent_after,
            url_path_before=old_url_path,
            url_path_after=new_url_path,
        )

        # Only commit when all descendants are properly updated
        with transaction.atomic():
            # Allow treebeard to update `path` values
            MP_MoveHandler(page, target, self.pos).process()

            # Treebeard's move method doesn't actually update the in-memory instance,
            # so we need to work with a freshly loaded one now
            new_page = Page.objects.get(id=page.id)
            new_page.url_path = new_url_path
            new_page.save()

            # Update descendant paths if url_path has changed
            if url_path_changed:
                new_page._update_descendant_url_paths(old_url_path, new_url_path)

        # Emit post_page_move signal
        post_page_move.send(
            sender=page.specific_class or page.__class__,
            instance=new_page,
            parent_page_before=parent_before,
            parent_page_after=parent_after,
            url_path_before=old_url_path,
            url_path_after=new_url_path,
        )

        # Log
        log(
            instance=page,
            action="wagtail.move" if url_path_changed else "wagtail.reorder",
            user=self.user,
            data={
                "source": {
                    "id": parent_before.id,
                    "title": parent_before.specific_deferred.get_admin_display_title(),
                },
                "destination": {
                    "id": parent_after.id,
                    "title": parent_after.specific_deferred.get_admin_display_title(),
                },
            },
        )
        logger.info('Page moved: "%s" id=%d path=%s', page.title, page.id, new_url_path)

    def execute(self, skip_permission_checks=False):
        if self.pos in ("first-child", "last-child", "sorted-child"):
            parent_after = self.target
        else:
            parent_after = self.target.get_parent()

        self.check(parent_after, skip_permission_checks=skip_permission_checks)

        return self._move_page(self.page, self.target, parent_after)
