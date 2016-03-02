from django.conf.urls import url
from wagtail.contrib.modeladmin.options import ModelAdmin
from wagtail.contrib.modeladmin.helpers import (
    get_object_specific_url_pattern, get_url_name)
from .helpers import TreebeardPermissionHelper, TreebeardButtonHelper
from .views import TreebeardCreateView, TreebeardMoveView


class TreebeardModelAdmin(ModelAdmin):
    """
    A custom ModelAdmin class for working with tree-based models that
    extend Treebeard's `MP_Node` model.
    """
    create_view_class = TreebeardCreateView
    permission_helper_class = TreebeardPermissionHelper
    button_helper_class = TreebeardButtonHelper
    move_form_select_indentation = True

    def move_view(self, request, object_id):
        kwargs = {'model_admin': self, 'object_id': object_id}
        return TreebeardMoveView.as_view(**kwargs)(request)

    def get_admin_urls_for_registration(self):
        urls = super(TreebeardModelAdmin, self).get_admin_urls_for_registration()
        urls.append(
            url(get_object_specific_url_pattern(self.opts, 'move'),
                self.move_view, name=get_url_name(self.opts, 'move'))
        )
        return urls

    def get_extra_class_names_for_field_col(self, field_name, obj):
        classes = []
        if field_name == self.list_display[0]:
            classes.append('first-col depth-%s' % obj.depth)
        return classes

    def get_index_view_extra_css(self):
        css = super(TreebeardModelAdmin, self).get_index_view_extra_css()
        css.append('modeladmin/recipes/treebeard/css/index.css')
        return css

    def get_templates(self, action='index'):
        app = self.opts.app_label
        model_name = self.opts.model_name
        return [
            'modeladmin/%s/%s/%s.html' % (app, model_name, action),
            'modeladmin/%s/%s.html' % (app, action),
            'modeladmin/recipes/treebeard/%s.html' % (action,),
            'modeladmin/%s.html' % (action,),
        ]
