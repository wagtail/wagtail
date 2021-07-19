from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.db import models
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.core.log_actions import LogFormatter
from wagtail.core.models import ModelLogEntry, Page, PageLogEntry, PageViewRestriction
from wagtail.core.rich_text.pages import PageLinkHandler
from wagtail.core.utils import get_content_languages


def require_wagtail_login(next):
    login_url = getattr(settings, 'WAGTAIL_FRONTEND_LOGIN_URL', reverse('wagtailcore_login'))
    return redirect_to_login(next, login_url)


@hooks.register('before_serve_page')
def check_view_restrictions(page, request, serve_args, serve_kwargs):
    """
    Check whether there are any view restrictions on this page which are
    not fulfilled by the given request object. If there are, return an
    HttpResponse that will notify the user of that restriction (and possibly
    include a password / login form that will allow them to proceed). If
    there are no such restrictions, return None
    """
    for restriction in page.get_view_restrictions():
        if not restriction.accept_request(request):
            if restriction.restriction_type == PageViewRestriction.PASSWORD:
                from wagtail.core.forms import PasswordViewRestrictionForm
                form = PasswordViewRestrictionForm(instance=restriction,
                                                   initial={'return_url': request.get_full_path()})
                action_url = reverse('wagtailcore_authenticate_with_password', args=[restriction.id, page.id])
                return page.serve_password_required_response(request, form, action_url)

            elif restriction.restriction_type in [PageViewRestriction.LOGIN, PageViewRestriction.GROUPS]:
                return require_wagtail_login(next=request.get_full_path())


@hooks.register('register_rich_text_features')
def register_core_features(features):
    features.default_features.append('hr')

    features.default_features.append('link')
    features.register_link_type(PageLinkHandler)

    features.default_features.append('bold')

    features.default_features.append('italic')

    features.default_features.extend(['h2', 'h3', 'h4'])

    features.default_features.append('ol')

    features.default_features.append('ul')


if getattr(settings, 'WAGTAIL_WORKFLOW_ENABLED', True):
    @hooks.register('register_permissions')
    def register_workflow_permissions():
        return Permission.objects.filter(
            content_type__app_label='wagtailcore',
            codename__in=['add_workflow', 'change_workflow', 'delete_workflow']
        )

    @hooks.register('register_permissions')
    def register_task_permissions():
        return Permission.objects.filter(
            content_type__app_label='wagtailcore',
            codename__in=['add_task', 'change_task', 'delete_task']
        )


@hooks.register('describe_collection_contents')
def describe_collection_children(collection):
    descendant_count = collection.get_descendants().count()
    if descendant_count:
        url = reverse('wagtailadmin_collections:index')
        return {
            'count': descendant_count,
            'count_text': ngettext(
                "%(count)s descendant collection",
                "%(count)s descendant collections",
                descendant_count
            ) % {'count': descendant_count},
            'url': url,
        }


@hooks.register('register_log_actions')
def register_core_log_actions(actions):
    actions.register_model(models.Model, ModelLogEntry)
    actions.register_model(Page, PageLogEntry)

    actions.register_action('wagtail.create', _('Create'), _('Created'))
    actions.register_action('wagtail.edit', _('Save draft'), _('Draft saved'))
    actions.register_action('wagtail.delete', _('Delete'), _('Deleted'))
    actions.register_action('wagtail.publish', _('Publish'), _('Published'))
    actions.register_action('wagtail.publish.scheduled', _("Publish scheduled draft"), _('Published scheduled draft'))
    actions.register_action('wagtail.unpublish', _('Unpublish'), _('Unpublished'))
    actions.register_action('wagtail.unpublish.scheduled', _('Unpublish scheduled draft'), _('Unpublished scheduled draft'))
    actions.register_action('wagtail.lock', _('Lock'), _('Locked'))
    actions.register_action('wagtail.unlock', _('Unlock'), _('Unlocked'))
    actions.register_action('wagtail.moderation.approve', _('Approve'), _('Approved'))
    actions.register_action('wagtail.moderation.reject', _('Reject'), _('Rejected'))

    @actions.register_action('wagtail.rename')
    class RenameActionFormatter(LogFormatter):
        label = _('Rename')

        def format_message(self, log_entry):
            try:
                return _("Renamed from '%(old)s' to '%(new)s'") % {
                    'old': log_entry.data['title']['old'],
                    'new': log_entry.data['title']['new'],
                }
            except KeyError:
                return _('Renamed')

    @actions.register_action('wagtail.revert')
    class RevertActionFormatter(LogFormatter):
        label = _('Revert')

        def format_message(self, log_entry):
            try:
                return _('Reverted to previous revision with id %(revision_id)s from %(created_at)s') % {
                    'revision_id': log_entry.data['revision']['id'],
                    'created_at': log_entry.data['revision']['created'],
                }
            except KeyError:
                return _('Reverted to previous revision')

    @actions.register_action('wagtail.copy')
    class CopyActionFormatter(LogFormatter):
        label = _('Copy')

        def format_message(self, log_entry):
            try:
                return _('Copied from %(title)s') % {
                    'title': log_entry.data['source']['title'],
                }
            except KeyError:
                return _("Copied")

    @actions.register_action('wagtail.copy_for_translation')
    class CopyForTranslationActionFormatter(LogFormatter):
        label = _('Copy for translation')

        def format_message(self, log_entry):
            try:
                return _('Copied for translation from %(title)s (%(locale)s)') % {
                    'title': log_entry.data['source']['title'],
                    'locale': get_content_languages().get(log_entry.data['source_locale']['language_code']) or '',
                }
            except KeyError:
                return _("Copied for translation")

    @actions.register_action('wagtail.create_alias')
    class CreateAliasActionFormatter(LogFormatter):
        label = _('Create alias')

        def format_message(self, log_entry):
            try:
                return _('Created an alias of %(title)s') % {
                    'title': log_entry.data['source']['title'],
                }
            except KeyError:
                return _("Created an alias")

    @actions.register_action('wagtail.convert_alias')
    class ConvertAliasActionFormatter(LogFormatter):
        label = _('Convert alias into ordinary page')

        def format_message(self, log_entry):
            try:
                return _("Converted the alias '%(title)s' into an ordinary page") % {
                    'title': log_entry.data['page']['title'],
                }
            except KeyError:
                return _("Converted an alias into an ordinary page")

    @actions.register_action('wagtail.move')
    class MoveActionFormatter(LogFormatter):
        label = _('Move')

        def format_message(self, log_entry):
            try:
                return _("Moved from '%(old_parent)s' to '%(new_parent)s'") % {
                    'old_parent': log_entry.data['source']['title'],
                    'new_parent': log_entry.data['destination']['title'],
                }
            except KeyError:
                return _('Moved')

    @actions.register_action('wagtail.reorder')
    class ReorderActionFormatter(LogFormatter):
        label = _('Reorder')

        def format_message(self, log_entry):
            try:
                return _("Reordered under '%(parent)s'") % {
                    'parent': log_entry.data['destination']['title'],
                }
            except KeyError:
                return _('Reordered')

    @actions.register_action('wagtail.publish.schedule')
    class SchedulePublishActionFormatter(LogFormatter):
        label = _("Schedule publication")

        def format_message(self, log_entry):
            try:
                if log_entry.data['revision']['has_live_version']:
                    return _('Revision %(revision_id)s from %(created_at)s scheduled for publishing at %(go_live_at)s.') % {
                        'revision_id': log_entry.data['revision']['id'],
                        'created_at': log_entry.data['revision']['created'],
                        'go_live_at': log_entry.data['revision']['go_live_at'],
                    }
                else:
                    return _('Page scheduled for publishing at %(go_live_at)s') % {
                        'go_live_at': log_entry.data['revision']['go_live_at'],
                    }
            except KeyError:
                return _('Page scheduled for publishing')

    @actions.register_action('wagtail.schedule.cancel')
    class UnschedulePublicationActionFormatter(LogFormatter):
        label = _("Unschedule publication")

        def format_message(self, log_entry):
            try:
                if log_entry.data['revision']['has_live_version']:
                    return _('Revision %(revision_id)s from %(created_at)s unscheduled from publishing at %(go_live_at)s.') % {
                        'revision_id': log_entry.data['revision']['id'],
                        'created_at': log_entry.data['revision']['created'],
                        'go_live_at': log_entry.data['revision']['go_live_at'],
                    }
                else:
                    return _('Page unscheduled for publishing at %(go_live_at)s') % {
                        'go_live_at': log_entry.data['revision']['go_live_at'],
                    }
            except KeyError:
                return _('Page unscheduled from publishing')

    @actions.register_action('wagtail.view_restriction.create')
    class AddViewRestrictionActionFormatter(LogFormatter):
        label = _("Add view restrictions")

        def format_message(self, log_entry):
            try:
                return _("Added the '%(restriction)s' view restriction") % {
                    'restriction': log_entry.data['restriction']['title'],
                }
            except KeyError:
                return _('Added view restriction')

    @actions.register_action('wagtail.view_restriction.edit')
    class EditViewRestrictionActionFormatter(LogFormatter):
        label = _("Update view restrictions")

        def format_message(self, log_entry):
            try:
                return _("Updated the view restriction to '%(restriction)s'") % {
                    'restriction': log_entry.data['restriction']['title'],
                }
            except KeyError:
                return _('Updated view restriction')

    @actions.register_action('wagtail.view_restriction.delete')
    class DeleteViewRestrictionActionFormatter(LogFormatter):
        label = _("Remove view restrictions")

        def format_message(self, log_entry):
            try:
                return _("Removed the '%(restriction)s' view restriction") % {
                    'restriction': log_entry.data['restriction']['title'],
                }
            except KeyError:
                return _('Removed view restriction')

    class CommentLogFormatter(LogFormatter):
        @staticmethod
        def _field_label_from_content_path(model, content_path):
            """
            Finds the translated field label for the given model and content path

            Raises LookupError if not found
            """
            field_name = content_path.split('.')[0]
            return capfirst(model._meta.get_field(field_name).verbose_name)

    @actions.register_action('wagtail.comments.create')
    class CreateCommentActionFormatter(CommentLogFormatter):
        label = _('Add comment')

        def format_message(self, log_entry):
            try:
                return _('Added a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['comment']['text'],
                }
            except KeyError:
                return _('Added a comment')

    @actions.register_action('wagtail.comments.edit')
    class EditCommentActionFormatter(CommentLogFormatter):
        label = _('Edit comment')

        def format_message(self, log_entry):
            try:
                return _('Edited a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['comment']['text'],
                }
            except KeyError:
                return _("Edited a comment")

    @actions.register_action('wagtail.comments.delete')
    class DeleteCommentActionFormatter(CommentLogFormatter):
        label = _('Delete comment')

        def format_message(self, log_entry):
            try:
                return _('Deleted a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['comment']['text'],
                }
            except KeyError:
                return _("Deleted a comment")

    @actions.register_action('wagtail.comments.resolve')
    class ResolveCommentActionFormatter(CommentLogFormatter):
        label = _('Resolve comment')

        def format_message(self, log_entry):
            try:
                return _('Resolved a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['comment']['text'],
                }
            except KeyError:
                return _("Resolved a comment")

    @actions.register_action('wagtail.comments.create_reply')
    class CreateReplyActionFormatter(CommentLogFormatter):
        label = _('Reply to comment')

        def format_message(self, log_entry):
            try:
                return _('Replied to comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['reply']['text'],
                }
            except KeyError:
                return _('Replied to a comment')

    @actions.register_action('wagtail.comments.edit_reply')
    class EditReplyActionFormatter(CommentLogFormatter):
        label = _('Edit reply to comment')

        def format_message(self, log_entry):
            try:
                return _('Edited a reply to a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['reply']['text'],
                }
            except KeyError:
                return _("Edited a reply")

    @actions.register_action('wagtail.comments.delete_reply')
    class DeleteReplyActionFormatter(CommentLogFormatter):
        label = _('Delete reply to comment')

        def format_message(self, log_entry):
            try:
                return _('Deleted a reply to a comment on field %(field)s: "%(text)s"') % {
                    'field': self._field_label_from_content_path(log_entry.page.specific_class, log_entry.data['comment']['contentpath']),
                    'text': log_entry.data['reply']['text'],
                }
            except KeyError:
                return _("Deleted a reply")


@hooks.register('register_log_actions')
def register_workflow_log_actions(actions):

    class WorkflowLogFormatter(LogFormatter):
        def format_comment(self, log_entry):
            return log_entry.data.get('comment', '')

    @actions.register_action('wagtail.workflow.start')
    class StartWorkflowActionFormatter(WorkflowLogFormatter):
        label = _('Workflow: start')

        def format_message(self, log_entry):
            try:
                return _("'%(workflow)s' started. Next step '%(task)s'") % {
                    'workflow': log_entry.data['workflow']['title'],
                    'task': log_entry.data['workflow']['next']['title'],
                }
            except (KeyError, TypeError):
                return _('Workflow started')

    @actions.register_action('wagtail.workflow.approve')
    class ApproveWorkflowActionFormatter(WorkflowLogFormatter):
        label = _('Workflow: approve task')

        def format_message(self, log_entry):
            try:
                if log_entry.data['workflow']['next']:
                    return _("Approved at '%(task)s'. Next step '%(next_task)s'") % {
                        'task': log_entry.data['workflow']['task']['title'],
                        'next_task': log_entry.data['workflow']['next']['title'],
                    }
                else:
                    return _("Approved at '%(task)s'. '%(workflow)s' complete") % {
                        'task': log_entry.data['workflow']['task']['title'],
                        'workflow': log_entry.data['workflow']['title'],
                    }
            except (KeyError, TypeError):
                return _('Workflow task approved')

    @actions.register_action('wagtail.workflow.reject')
    class RejectWorkflowActionFormatter(WorkflowLogFormatter):
        label = _('Workflow: reject task')

        def format_message(self, log_entry):
            try:
                return _("Rejected at '%(task)s'. Changes requested") % {
                    'task': log_entry.data['workflow']['task']['title'],
                }
            except (KeyError, TypeError):
                return _('Workflow task rejected. Workflow complete')

    @actions.register_action('wagtail.workflow.resume')
    class ResumeWorkflowActionFormatter(WorkflowLogFormatter):
        label = _('Workflow: resume task')

        def format_message(self, log_entry):
            try:
                return _("Resubmitted '%(task)s'. Workflow resumed'") % {
                    'task': log_entry.data['workflow']['task']['title'],
                }
            except (KeyError, TypeError):
                return _('Workflow task resubmitted. Workflow resumed')

    @actions.register_action('wagtail.workflow.cancel')
    class CancelWorkflowActionFormatter(WorkflowLogFormatter):
        label = _('Workflow: cancel')

        def format_message(self, log_entry):
            try:
                return _("Cancelled '%(workflow)s' at '%(task)s'") % {
                    'workflow': log_entry.data['workflow']['title'],
                    'task': log_entry.data['workflow']['task']['title'],
                }
            except (KeyError, TypeError):
                return _('Workflow cancelled')
