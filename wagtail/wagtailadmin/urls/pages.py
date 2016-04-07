from __future__ import absolute_import, unicode_literals

from django.conf.urls import url

from wagtail.wagtailadmin.views import page_privacy, pages

urlpatterns = [
    url(r'^add/(\w+)/(\w+)/(\d+)/$', pages.create, name='add'),
    url(r'^add/(\w+)/(\w+)/(\d+)/preview/$', pages.preview_on_create, name='preview_on_add'),
    url(r'^usage/(\w+)/(\w+)/$', pages.content_type_use, name='type_use'),

    url(r'^(\d+)/edit/$', pages.edit, name='edit'),
    url(r'^(\d+)/edit/preview/$', pages.preview_on_edit, name='preview_on_edit'),

    url(r'^preview/$', pages.preview, name='preview'),
    url(r'^preview_loading/$', pages.preview_loading, name='preview_loading'),

    url(r'^(\d+)/view_draft/$', pages.view_draft, name='view_draft'),
    url(r'^(\d+)/add_subpage/$', pages.add_subpage, name='add_subpage'),
    url(r'^(\d+)/delete/$', pages.delete, name='delete'),
    url(r'^(\d+)/unpublish/$', pages.unpublish, name='unpublish'),

    url(r'^search/$', pages.search, name='search'),

    url(r'^(\d+)/move/$', pages.move_choose_destination, name='move'),
    url(r'^(\d+)/move/(\d+)/$', pages.move_choose_destination, name='move_choose_destination'),
    url(r'^(\d+)/move/(\d+)/confirm/$', pages.move_confirm, name='move_confirm'),
    url(r'^(\d+)/set_position/$', pages.set_page_position, name='set_page_position'),

    url(r'^(\d+)/copy/$', pages.copy, name='copy'),

    url(r'^moderation/(\d+)/approve/$', pages.approve_moderation, name='approve_moderation'),
    url(r'^moderation/(\d+)/reject/$', pages.reject_moderation, name='reject_moderation'),
    url(r'^moderation/(\d+)/preview/$', pages.preview_for_moderation, name='preview_for_moderation'),

    url(r'^(\d+)/privacy/$', page_privacy.set_privacy, name='set_privacy'),

    url(r'^(\d+)/lock/$', pages.lock, name='lock'),
    url(r'^(\d+)/unlock/$', pages.unlock, name='unlock'),

    url(r'^(\d+)/revisions/$', pages.revisions_index, name='revisions_index'),
    url(r'^(\d+)/revisions/(\d+)/view/$', pages.revisions_view, name='revisions_view'),
    url(r'^(\d+)/revisions/(\d+)/revert/$', pages.revisions_revert, name='revisions_revert'),
]
