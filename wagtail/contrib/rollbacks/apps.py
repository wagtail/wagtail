"""
Contains application configuration.
"""
import logging

from django.apps import apps
from django.contrib.admin.apps import SimpleAdminConfig
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from wagtailplus.utils.edit_handlers import add_panel_to_edit_handler

from wagtailplus.wagtailrollbacks.edit_handlers import HistoryPanel


logger = logging.getLogger('wagtail.core')


class WagtailRollbacksAppConfig(SimpleAdminConfig):
    name = 'wagtail.contrib.rollbacks'
    label = 'wagtailrollbacks'
    verbose_name = 'Rollbacks'

    @cached_property
    def applicable_models(self):
        """
        Returns a list of model classes that subclass Page.

        :rtype: list.
        """
        Page = apps.get_model('wagtailcore', 'Page')
        applicable = []

        for model in apps.get_models():
            if issubclass(model, Page):
                applicable.append(model)

        return applicable

    def add_rollback_panels(self):
        """
        Adds rollback panel to applicable model class's edit handlers.
        """
        for model in self.applicable_models:
            add_panel_to_edit_handler(model, HistoryPanel, _(u'History'))

    @staticmethod
    def add_rollback_methods():
        """
        Adds rollback methods to applicable model classes.
        """
        # Modified Page.save_revision method.
        def page_rollback(instance, revision_id, user=None, submitted_for_moderation=False, approved_go_live_at=None, changed=True):
            old_revision = instance.revisions.get(pk=revision_id)
            new_revision = instance.revisions.create(
                content_json=old_revision.content_json,
                user=user,
                submitted_for_moderation=submitted_for_moderation,
                approved_go_live_at=approved_go_live_at
            )

            update_fields = []

            instance.latest_revision_created_at = new_revision.created_at
            update_fields.append('latest_revision_created_at')

            if changed:
                instance.has_unpublished_changes = True
                update_fields.append('has_unpublished_changes')

            if update_fields:
                instance.save(update_fields=update_fields)

            logger.info(
                "Page edited: \"%s\" id=%d revision_id=%d",
                instance.title,
                instance.id,
                new_revision.id
            )

            if submitted_for_moderation:
                logger.info(
                    "Page submitted for moderation: \"%s\" id=%d revision_id=%d",
                    instance.title,
                    instance.id,
                    new_revision.id
                )

            return new_revision

        Page = apps.get_model('wagtailcore', 'Page')
        Page.add_to_class('rollback', page_rollback)

    def ready(self):
        """
        Finalizes application configuration.
        """
        self.add_rollback_panels()
        self.add_rollback_methods()
        super(WagtailRollbacksAppConfig, self).ready()
