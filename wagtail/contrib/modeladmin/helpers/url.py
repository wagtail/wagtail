from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import urlquote


class AdminURLHelper:

    def __init__(self, model):
        self.model = model
        self.opts = model._meta

    def _get_action_url_pattern(self, action):
        if action == 'index':
            return r'^%s/%s/$' % (self.opts.app_label, self.opts.model_name)
        return r'^%s/%s/%s/$' % (self.opts.app_label, self.opts.model_name,
                                 action)

    def _get_object_specific_action_url_pattern(self, action):
        return r'^%s/%s/%s/(?P<instance_pk>[-\w]+)/$' % (
            self.opts.app_label, self.opts.model_name, action)

    def get_action_url_pattern(self, action):
        if action in ('create', 'choose_parent', 'index'):
            return self._get_action_url_pattern(action)
        return self._get_object_specific_action_url_pattern(action)

    def get_action_url_name(self, action):
        return '%s_%s_modeladmin_%s' % (
            self.opts.app_label, self.opts.model_name, action)

    def get_action_url(self, action, *args, **kwargs):
        if action in ('create', 'choose_parent', 'index'):
            return reverse(self.get_action_url_name(action))
        url_name = self.get_action_url_name(action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @cached_property
    def index_url(self):
        return self.get_action_url('index')

    @cached_property
    def create_url(self):
        return self.get_action_url('create')


class PageAdminURLHelper(AdminURLHelper):

    def get_action_url(self, action, *args, **kwargs):
        if action in ('add', 'edit', 'delete', 'unpublish', 'copy'):
            url_name = 'wagtailadmin_pages:%s' % action
            target_url = reverse(url_name, args=args, kwargs=kwargs)
            return '%s?next=%s' % (target_url, urlquote(self.index_url))
        return super().get_action_url(action, *args, **kwargs)
