from urllib.parse import quote

from django.contrib.admin.utils import quote as admin_quote
from django.urls import reverse
from django.utils.functional import cached_property


class AdminURLHelper:
    def __init__(self, model, base_url_path=None):
        self.model = model
        self.opts = model._meta
        self.base_url_path = self._get_base_url_path(base_url_path)

    def _get_base_url_path(self, base_url_path):
        if base_url_path:
            return base_url_path.strip().strip("/")
        return r"%s/%s" % (self.opts.app_label, self.opts.model_name)

    def _get_action_url_pattern(self, action):
        if action == "index":
            return r"^%s/$" % (self.base_url_path)
        return r"^%s/%s/$" % (self.base_url_path, action)

    def _get_object_specific_action_url_pattern(self, action):
        return r"^%s/%s/(?P<instance_pk>[-\w]+)/$" % (
            self.base_url_path,
            action,
        )

    def get_action_url_pattern(self, action):
        if action in ("create", "choose_parent", "index"):
            return self._get_action_url_pattern(action)
        return self._get_object_specific_action_url_pattern(action)

    def get_action_url_name(self, action):
        return "%s_modeladmin_%s" % (
            self.base_url_path.replace("/", "_"),
            action,
        )

    def get_action_url(self, action, *args, **kwargs):
        if action in ("create", "choose_parent", "index"):
            return reverse(self.get_action_url_name(action))
        url_name = self.get_action_url_name(action)
        return reverse(url_name, args=args, kwargs=kwargs)

    @cached_property
    def index_url(self):
        return self.get_action_url("index")

    @cached_property
    def create_url(self):
        return self.get_action_url("create")


# for registering with wagtail.admin.admin_url_finder.
# Subclasses should define url_helper and permission_helper
class ModelAdminURLFinder:
    def __init__(self, user):
        self.user = user

    def get_edit_url(self, instance):
        if self.user is None or self.permission_helper.user_can_edit_obj(
            self.user, instance
        ):
            return self.url_helper.get_action_url("edit", admin_quote(instance.pk))


class PageAdminURLHelper(AdminURLHelper):
    def get_action_url(self, action, *args, **kwargs):
        if action in ("add", "edit", "delete", "unpublish", "copy", "history"):
            url_name = "wagtailadmin_pages:%s" % action
            target_url = reverse(url_name, args=args, kwargs=kwargs)
            return "%s?next=%s" % (target_url, quote(self.index_url))
        return super().get_action_url(action, *args, **kwargs)
