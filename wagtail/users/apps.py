from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailUsersAppConfig(AppConfig):
    name = "wagtail.users"
    label = "wagtailusers"
    verbose_name = _("Wagtail users")
    default_auto_field = "django.db.models.AutoField"
    group_viewset = "wagtail.users.views.groups.GroupViewSet"
    user_viewset = "wagtail.users.views.users.UserViewSet"

    def ready(self):
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group

        from wagtail.permissions import register_permission_policy

        User = get_user_model()
        register_permission_policy(User)
        register_permission_policy(Group)
