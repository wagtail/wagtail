from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WagtailSnippetsTestsAppConfig(AppConfig):
    default_auto_field = "django.db.models.AutoField"
    name = "wagtail.test.snippets"
    label = "snippetstests"
    verbose_name = _("Wagtail snippets tests")

    def ready(self):
        # Test registration of permission order within the group permissions view,
        # as per https://docs.wagtail.org/en/stable/extending/customizing_group_views.html#customizing-the-group-editor-permissions-ordering
        # Invoking `register` from `ready` confirms that it does not perform any database queries -
        # if it did, it would fail (on a standard test run without --keepdb at least) because the
        # test database hasn't been migrated yet.
        from wagtail.users.permission_order import register

        register("snippetstests.fancysnippet", order=999)
