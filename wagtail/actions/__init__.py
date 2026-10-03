import swapper
from django.db import models

from wagtail.actions.base import BaseAction
from wagtail.actions.convert_alias import ConvertAliasPageAction
from wagtail.actions.copy_for_translation import (
    CopyForTranslationAction,
    CopyPageForTranslationAction,
)
from wagtail.actions.copy_page import CopyPageAction
from wagtail.actions.create import CreateAction, CreatePermissionError
from wagtail.actions.create_alias import CreatePageAliasAction
from wagtail.actions.create_page import CreatePageAction
from wagtail.actions.delete import DeleteAction, DeletePermissionError
from wagtail.actions.delete_page import DeletePageAction
from wagtail.actions.edit import EditAction, EditPermissionError
from wagtail.actions.edit_page import EditPageAction
from wagtail.actions.move_page import MovePageAction
from wagtail.actions.publish_page_revision import PublishPageRevisionAction
from wagtail.actions.publish_revision import PublishRevisionAction
from wagtail.actions.registry import ActionRegistry, action_registry
from wagtail.actions.revert_to_page_revision import RevertToPageRevisionAction
from wagtail.actions.revert_to_revision import RevertToRevisionAction
from wagtail.actions.unpublish import UnpublishAction
from wagtail.actions.unpublish_page import UnpublishPageAction

__all__ = [
    "BaseAction",
    "ConvertAliasPageAction",
    "CopyForTranslationAction",
    "CopyPageAction",
    "CopyPageForTranslationAction",
    "CreateAction",
    "CreatePageAction",
    "CreatePageAliasAction",
    "CreatePermissionError",
    "DeletePageAction",
    "EditAction",
    "EditPageAction",
    "EditPermissionError",
    "DeleteAction",
    "DeletePermissionError",
    "MovePageAction",
    "PublishRevisionAction",
    "PublishPageRevisionAction",
    "RevertToPageRevisionAction",
    "RevertToRevisionAction",
    "UnpublishAction",
    "UnpublishPageAction",
    "ActionRegistry",
    "action_registry",
]


def register_default_actions():
    from wagtail.models.draft_state import DraftStateMixin
    from wagtail.models.i18n import TranslatableMixin
    from wagtail.models.revisions import RevisionMixin

    Page = swapper.load_model("wagtailcore", "Page")

    action_registry.register(models.Model, CreateAction)
    action_registry.register(models.Model, EditAction)
    action_registry.register(models.Model, DeleteAction)

    action_registry.register(RevisionMixin, RevertToRevisionAction)

    action_registry.register(DraftStateMixin, PublishRevisionAction)
    action_registry.register(DraftStateMixin, UnpublishAction)

    action_registry.register(TranslatableMixin, CopyForTranslationAction)

    action_registry.register(Page, CreatePageAction)
    action_registry.register(Page, EditPageAction)
    action_registry.register(Page, DeletePageAction)
    action_registry.register(Page, CopyPageAction)
    action_registry.register(Page, MovePageAction)
    action_registry.register(Page, PublishPageRevisionAction)
    action_registry.register(Page, UnpublishPageAction)
    action_registry.register(Page, RevertToPageRevisionAction)
    action_registry.register(Page, ConvertAliasPageAction)
    action_registry.register(Page, CreatePageAliasAction)
    action_registry.register(Page, CopyPageForTranslationAction)
