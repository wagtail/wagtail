from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin

from wagtail.wagtailcore.models import Site, Page, GroupPagePermission

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
