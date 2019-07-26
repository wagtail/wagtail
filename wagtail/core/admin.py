
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

from wagtail.core.models import GroupPagePermission, Page, Site

if hasattr(settings, 'WAGTAIL_SITE_MODEL') and settings.WAGTAIL_SITE_MODEL != 'wagtailcore.Site':
    # This installation provides its own custom site class;
    # to avoid confusion, we won't expose the unused wagtailcore.Site class
    # in the admin.
    pass
else:
    admin.site.register(Site)


admin.site.register(Page)


# Extend GroupAdmin to include page permissions as an inline
class GroupPagePermissionInline(admin.TabularInline):
    model = GroupPagePermission
    raw_id_fields = ['page']
    verbose_name = 'page permission'
    verbose_name_plural = 'page permissions'


class GroupAdminWithPagePermissions(GroupAdmin):
    inlines = GroupAdmin.inlines + [GroupPagePermissionInline]


if admin.site.is_registered(Group):
    admin.site.unregister(Group)
admin.site.register(Group, GroupAdminWithPagePermissions)
