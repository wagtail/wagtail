from django.urls import re_path

from wagtail.admin.views import page_privacy, pages

app_name = 'wagtailadmin_pages'
urlpatterns = [
    re_path(r'^add/(\w+)/(\w+)/(\d+)/$', pages.create, name='add'),
    re_path(r'^add/(\w+)/(\w+)/(\d+)/preview/$', pages.PreviewOnCreate.as_view(), name='preview_on_add'),
    re_path(r'^usage/(\w+)/(\w+)/$', pages.content_type_use, name='type_use'),

    re_path(r'^(\d+)/edit/$', pages.edit, name='edit'),
    re_path(r'^(\d+)/edit/preview/$', pages.PreviewOnEdit.as_view(), name='preview_on_edit'),

    re_path(r'^(\d+)/view_draft/$', pages.view_draft, name='view_draft'),
    re_path(r'^(\d+)/add_subpage/$', pages.add_subpage, name='add_subpage'),
    re_path(r'^(\d+)/delete/$', pages.delete, name='delete'),
    re_path(r'^(\d+)/unpublish/$', pages.unpublish, name='unpublish'),

    re_path(r'^search/$', pages.search, name='search'),

    re_path(r'^(\d+)/move/$', pages.move_choose_destination, name='move'),
    re_path(r'^(\d+)/move/(\d+)/$', pages.move_choose_destination, name='move_choose_destination'),
    re_path(r'^(\d+)/move/(\d+)/confirm/$', pages.move_confirm, name='move_confirm'),
    re_path(r'^(\d+)/set_position/$', pages.set_page_position, name='set_page_position'),

    re_path(r'^(\d+)/copy/$', pages.copy, name='copy'),

    re_path(r'^moderation/(\d+)/approve/$', pages.approve_moderation, name='approve_moderation'),
    re_path(r'^moderation/(\d+)/reject/$', pages.reject_moderation, name='reject_moderation'),
    re_path(r'^moderation/(\d+)/preview/$', pages.preview_for_moderation, name='preview_for_moderation'),

    re_path(r'^(\d+)/privacy/$', page_privacy.set_privacy, name='set_privacy'),

    re_path(r'^(\d+)/lock/$', pages.lock, name='lock'),
    re_path(r'^(\d+)/unlock/$', pages.unlock, name='unlock'),

    re_path(r'^(\d+)/revisions/$', pages.revisions_index, name='revisions_index'),
    re_path(r'^(\d+)/revisions/(\d+)/view/$', pages.revisions_view, name='revisions_view'),
    re_path(r'^(\d+)/revisions/(\d+)/revert/$', pages.revisions_revert, name='revisions_revert'),
    re_path(r'^(\d+)/revisions/(\d+)/unschedule/$', pages.revisions_unschedule, name='revisions_unschedule'),
    re_path(r'^(\d+)/revisions/compare/(live|earliest|\d+)\.\.\.(live|latest|\d+)/$', pages.revisions_compare, name='revisions_compare'),
]
