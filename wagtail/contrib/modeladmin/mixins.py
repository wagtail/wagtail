from __future__ import absolute_import, unicode_literals

from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.db.models import F
from django.forms.widgets import flatatt
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from wagtail.wagtailcore.models import Orderable
from wagtail.wagtailimages.models import Filter


class ThumbnailMixin(object):
    """
    Mixin class to help display thumbnail images in ModelAdmin listing results.
    `thumb_image_field_name` must be overridden to name a ForeignKey field on
    your model, linking to `wagtailimages.Image`.
    """
    thumb_image_field_name = 'image'
    thumb_image_filter_spec = 'fill-100x100'
    thumb_image_width = 50
    thumb_classname = 'admin-thumb'
    thumb_col_header_text = _('image')
    thumb_default = None

    def admin_thumb(self, obj):
        try:
            image = getattr(obj, self.thumb_image_field_name, None)
        except AttributeError:
            raise ImproperlyConfigured(
                u"The `thumb_image_field_name` attribute on your `%s` class "
                "must name a field on your model." % self.__class__.__name__
            )

        img_attrs = {
            'src': self.thumb_default,
            'width': self.thumb_image_width,
            'class': self.thumb_classname,
        }
        if image:
            fltr, _ = Filter.objects.get_or_create(
                spec=self.thumb_image_filter_spec)
            img_attrs.update({'src': image.get_rendition(fltr).url})
            return mark_safe('<img{}>'.format(flatatt(img_attrs)))
        elif self.thumb_default:
            return mark_safe('<img{}>'.format(flatatt(img_attrs)))
        return ''
    admin_thumb.short_description = thumb_col_header_text

    def get_extra_attrs_for_field_col(self, obj, field_name):
        """
        Add a width attribute to the column to help with sizing (especially
        when used with OrderableMixin)
        """
        attrs = super(ThumbnailMixin, self).get_extra_attrs_for_field_col(
            obj, field_name)
        if field_name == 'admin_thumb':
            attrs['width'] = self.thumb_image_width
        return attrs


class OrderableMixin(object):
    """
    Mixin class to add drag-and-drop ordering support to the ModelAdmin listing
    view when the model extends the `wagtail.wagtailcore.models.Orderable`
    abstract model class.
    """
    def __init__(self, parent=None):
        super(OrderableMixin, self).__init__(parent)
        """
        Don't allow initialisation unless self.model subclasses
        `wagtail.wagtailcore.models.Orderable`
        """
        if not issubclass(self.model, Orderable):
            raise ImproperlyConfigured(
                u"You are using `OrderableMixin` for you '%s' class, but the "
                "specified model is not a sub-class of "
                "`wagtail.wagtailcore.models.Orderable`." %
                self.__class__.__name__)

    def get_list_display(self, request):
        """Add `index_order` as the first column to results"""
        list_display = super(OrderableMixin, self).get_list_display(request)
        if self.permission_helper.user_can_edit_obj(request.user, None):
            if type(list_display) is list:
                order_col_prepend = ['index_order']
            else:
                order_col_prepend = ('index_order', )
            return order_col_prepend + list_display
        return list_display

    def get_list_display_add_buttons(self, request):
        """
        If `list_display_add_buttons` isn't set, ensure the buttons are not
        added to the `index_order` column.
        """
        col_field_name = super(
            OrderableMixin, self).get_list_display_add_buttons(request)
        if col_field_name == 'index_order':
            list_display = self.get_list_display(request)
            return list_display[1]
        return col_field_name

    def get_extra_attrs_for_field_col(self, field_name, obj):
        """
        Add data attributes to the `index_order` column that can be picked
        up via JS. The PK isn't present elsewhere (yet!), and the title is
        used for adding success messages on completion.
        """
        attrs = super(OrderableMixin, self).get_extra_attrs_for_field_col(
            obj, field_name)
        if field_name == 'index_order':
            attrs.update({
                'data-obj-pk': obj.pk,
                'data-obj-title': obj.__str__(),
                'width': 20,
            })
        return attrs

    def get_extra_class_names_for_field_col(self, field_name, obj):
        """
        Add the `visible-on-drag` class to certain columns
        """
        classnames = super(OrderableMixin, self).get_extra_class_names_for_field_col(
            field_name, obj)
        if field_name in ('index_order', self.list_display[0], 'admin_thumb',
                          self.list_display_add_buttons or ''):
            classnames.append('visible-on-drag')
        return classnames

    def index_order(self, obj):
        """Content for the `index_order` column"""
        return mark_safe(
            '<div class="handle icon icon-grip text-replace" '
            'aria-hidden="true">Drag</div>'
        )
    index_order.admin_order_field = 'sort_order'
    index_order.short_description = _('Order')

    def reorder_view(self, request, instance_pk):
        """
        Very simple view functionality for updating the `sort_order` values
        for objects after a row has been dragged to a new position.
        """
        if not self.permission_helper.user_can_edit_obj(request.user, None):
            raise PermissionDenied
        obj_to_move = get_object_or_404(self.model, pk=instance_pk)
        position = request.GET.get('position', self.model.objects.count())
        position = int(position)
        old_position = obj_to_move.sort_order
        if int(position) < old_position:
            self.model.objects.filter(
                sort_order__lt=old_position,
                sort_order__gte=int(position)
            ).update(sort_order=F('sort_order') + 1)
        elif int(position) > old_position:
            self.model.objects.filter(
                sort_order__gt=old_position,
                sort_order__lte=int(position)
            ).update(sort_order=F('sort_order') - 1)
        obj_to_move.sort_order = position
        obj_to_move.save()
        return HttpResponse('Reordering was successful')

    def get_index_view_extra_css(self):
        css = super(OrderableMixin, self).get_index_view_extra_css()
        css.append('wagtailmodeladmin/css/orderablemixin.css')
        return css

    def get_index_view_extra_js(self):
        js = super(OrderableMixin, self).get_index_view_extra_js()
        js.append('wagtailmodeladmin/js/orderablemixin.js')
        return js

    def get_admin_urls_for_registration(self):
        urls = super(OrderableMixin, self).get_admin_urls_for_registration()
        urls += (
            url(
                self.url_helper.get_action_url_pattern('reorder'),
                view=self.reorder_view,
                name=self.url_helper.get_action_url_name('reorder')
            ),
        )
        return urls
