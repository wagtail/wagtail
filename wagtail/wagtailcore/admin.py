from __future__ import absolute_import, unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from wagtail.wagtailcore.models import GroupPagePermission, Page, Site

admin.site.register(Site)


# Use the Treebeard treeadmin.
class PageAdmin(TreeAdmin):
    form = movenodeform_factory(Page)


admin.site.register(Page, PageAdmin)


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
