from django.conf import settings
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from wagtail.core import hooks
from wagtail.core.models import PageViewRestriction
from wagtail.core.rich_text.pages import PageLinkHandler


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


@hooks.register('register_permissions')
def register_collection_permissions():
    return Permission.objects.filter(
        content_type__app_label='wagtailcore',
        codename__in=['add_collection', 'change_collection', 'delete_collection']
    )


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

    def revert_message(data):
        try:
            return _('Reverted to previous revision with id %(revision_id)s from %(created_at)s') % {
                'revision_id': data['revision']['id'],
                'created_at': data['revision']['created'],
            }
        except KeyError:
            return _('Reverted to previous revision')

    def copy_message(data):
        try:
            return _('Copied from %(title)s') % {
                'title': data['source']['title'],
            }
        except KeyError:
            return _("Copied")

    def create_alias_message(data):
        try:
            return _('Created an alias of %(title)s') % {
                'title': data['source']['title'],
            }
        except KeyError:
            return _("Created an alias")

    def convert_alias_message(data):
        try:
            return _("Converted the alias '%(title)s' into a regular page") % {
                'title': data['page']['title'],
            }
        except KeyError:
            return _("Converted an alias into a regular page")

    def move_message(data):
        try:
            return _("Moved from '%(old_parent)s' to '%(new_parent)s'") % {
                'old_parent': data['source']['title'],
                'new_parent': data['destination']['title'],
            }
        except KeyError:
            return _('Moved')

    def reorder_message(data):
        try:
            return _("Reordered under '%(parent)s'") % {
                'parent': data['destination']['title'],
            }
        except KeyError:
            return _('Reordered')

    def schedule_publish_message(data):
        try:
            if data['revision']['has_live_version']:
                return _('Revision %(revision_id)s from %(created_at)s scheduled for publishing at %(go_live_at)s.') % {
                    'revision_id': data['revision']['id'],
                    'created_at': data['revision']['created'],
                    'go_live_at': data['revision']['go_live_at'],
                }
            else:
                return _('Page scheduled for publishing at %(go_live_at)s') % {
                    'go_live_at': data['revision']['go_live_at'],
                }
        except KeyError:
            return _('Page scheduled for publishing')

    def unschedule_publish_message(data):
        try:
            if data['revision']['has_live_version']:
                return _('Revision %(revision_id)s from %(created_at)s unscheduled from publishing at %(go_live_at)s.') % {
                    'revision_id': data['revision']['id'],
                    'created_at': data['revision']['created'],
                    'go_live_at': data['revision']['go_live_at'],
                }
            else:
                return _('Page unscheduled for publishing at %(go_live_at)s') % {
                    'go_live_at': data['revision']['go_live_at'],
                }
        except KeyError:
            return _('Page unscheduled from publishing')

    def add_view_restriction(data):
        try:
            return _("Added the '%(restriction)s' view restriction") % {
                'restriction': data['restriction']['title'],
            }
        except KeyError:
            return _('Added view restriction')

    def edit_view_restriction(data):
        try:
            return _("Updated the view restriction to '%(restriction)s'") % {
                'restriction': data['restriction']['title'],
            }
        except KeyError:
            return _('Updated view restriction')

    def delete_view_restriction(data):
        try:
            return _("Removed the '%(restriction)s' view restriction") % {
                'restriction': data['restriction']['title'],
            }
        except KeyError:
            return _('Removed view restriction')

    def rename_message(data):
        try:
            return _("Renamed from '%(old)s' to '%(new)s'") % {
                'old': data['title']['old'],
                'new': data['title']['new'],
            }
        except KeyError:
            return _('Renamed')

    actions.register_action('wagtail.rename', _('Rename'), rename_message)
    actions.register_action('wagtail.revert', _('Revert'), revert_message)
    actions.register_action('wagtail.copy', _('Copy'), copy_message)
    actions.register_action('wagtail.create_alias', _('Create alias'), create_alias_message)
    actions.register_action('wagtail.convert_alias', _('Convert alias into regular page'), convert_alias_message)
    actions.register_action('wagtail.move', _('Move'), move_message)
    actions.register_action('wagtail.reorder', _('Reorder'), reorder_message)
    actions.register_action('wagtail.publish.schedule', _("Schedule publication"), schedule_publish_message)
    actions.register_action('wagtail.schedule.cancel', _("Unschedule publication"), unschedule_publish_message)
    actions.register_action('wagtail.view_restriction.create', _("Add view restrictions"), add_view_restriction)
    actions.register_action('wagtail.view_restriction.edit', _("Update view restrictions"), edit_view_restriction)
    actions.register_action('wagtail.view_restriction.delete', _("Remove view restrictions"), delete_view_restriction)


@hooks.register('register_log_actions')
def register_workflow_log_actions(actions):
    def workflow_start_message(data):
        try:
            return _("'%(workflow)s' started. Next step '%(task)s'") % {
                'workflow': data['workflow']['title'],
                'task': data['workflow']['next']['title'],
            }
        except (KeyError, TypeError):
            return _('Workflow started')

    def workflow_approve_message(data):
        try:
            if data['workflow']['next']:
                return _("Approved at '%(task)s'. Next step '%(next_task)s'") % {
                    'task': data['workflow']['task']['title'],
                    'next_task': data['workflow']['next']['title'],
                }
            else:
                return _("Approved at '%(task)s'. '%(workflow)s' complete") % {
                    'task': data['workflow']['task']['title'],
                    'workflow': data['workflow']['title'],
                }
        except (KeyError, TypeError):
            return _('Workflow task approved')

    def workflow_reject_message(data):
        try:
            return _("Rejected at '%(task)s'. Changes requested") % {
                'task': data['workflow']['task']['title'],
            }
        except (KeyError, TypeError):
            return _('Workflow task rejected. Workflow complete')

    def workflow_resume_message(data):
        try:
            return _("Resubmitted '%(task)s'. Workflow resumed'") % {
                'task': data['workflow']['task']['title'],
            }
        except (KeyError, TypeError):
            return _('Workflow task resubmitted. Workflow resumed')

    def workflow_cancel_message(data):
        try:
            return _("Cancelled '%(workflow)s' at '%(task)s'") % {
                'workflow': data['workflow']['title'],
                'task': data['workflow']['task']['title'],
            }
        except (KeyError, TypeError):
            return _('Workflow cancelled')

    actions.register_action('wagtail.workflow.start', _('Workflow: start'), workflow_start_message)
    actions.register_action('wagtail.workflow.approve', _('Workflow: approve task'), workflow_approve_message)
    actions.register_action('wagtail.workflow.reject', _('Workflow: reject task'), workflow_reject_message)
    actions.register_action('wagtail.workflow.resume', _('Workflow: resume task'), workflow_resume_message)
    actions.register_action('wagtail.workflow.cancel', _('Workflow: cancel'), workflow_cancel_message)
