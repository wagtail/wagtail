from django.utils.translation import ugettext as _
from django.utils.encoding import force_text
from django.contrib.admin.utils import quote
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


def get_url_pattern(model_meta, action=None):
    if not action:
        return r'^modeladmin/%s/%s/$' % (
            model_meta.app_label, model_meta.model_name)
    return r'^modeladmin/%s/%s/%s/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_object_specific_url_pattern(model_meta, action):
    return r'^modeladmin/%s/%s/%s/(?P<object_id>[-\w]+)/$' % (
        model_meta.app_label, model_meta.model_name, action)


def get_url_name(model_meta, action='index'):
    return '%s_%s_modeladmin_%s/' % (
        model_meta.app_label, model_meta.model_name, action)


def permission_denied(request):
    """Return a standard 'permission denied' response"""
    from wagtail.wagtailadmin import messages

    messages.error(
        request, _('Sorry, you do not have permission to access this area.'))
    return redirect('wagtailadmin_home')


class ActionButtonHelper(object):

    def __init__(self, model, permission_helper, user, obj):
        self.user = user
        self.model = model
        self.opts = model._meta
        self.permission_helper = permission_helper
        self.model_name = force_text(self.opts.verbose_name).lower()
        self.obj = obj
        self.pk = quote(getattr(obj, self.opts.pk.attname))

    def get_action_url(self, action):
        return reverse(get_url_name(self.opts, action), args=(self.pk,))

    def edit_button(self):
        return {
            'title': _('Edit this %s') % self.model_name,
            'label': _('Edit'),
            'url': self.get_action_url('edit'),
        }

    def delete_button(self):
        return {
            'title': _('Delete this %s') % self.model_name,
            'label': _('Delete'),
            'url': self.get_action_url('confirm_delete'),
        }

    def unpublish_button(self):
        return {
            'title': _('Unpublish this %s') % self.model_name,
            'label': _('Unpublish'),
            'url': self.get_action_url('unpublish'),
        }

    def copy_button(self):
        return {
            'title': _('Copy this %s') % self.model_name,
            'label': _('Copy'),
            'url': self.get_action_url('copy'),
        }

    def get_permitted_buttons(self):
        user = self.user
        obj = self.obj
        buttons = []
        if self.permission_helper.can_edit_object(user, obj):
            buttons.append(self.edit_button())
        if self.permission_helper.can_copy_object(user, obj):
            buttons.append(self.copy_button())
        if self.permission_helper.can_delete_object(user, obj):
            buttons.append(self.delete_button())
        if self.permission_helper.can_unpublish_object(user, obj):
            buttons.append(self.unpublish_button())
        return buttons
