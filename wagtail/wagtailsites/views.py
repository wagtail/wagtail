from django.utils.translation import ugettext_lazy as __

from wagtail.wagtailcore.models import Site
from wagtail.wagtailsites.forms import SiteForm
from wagtail.wagtailadmin.views.generic import IndexView, CreateView, EditView, DeleteView


class Index(IndexView):
    any_permission_required = ['wagtailcore.add_site', 'wagtailcore.change_site', 'wagtailcore.delete_site']
    model = Site
    context_object_name = 'sites'
    template = 'wagtailsites/index.html'


class Create(CreateView):
    permission_required = 'wagtailcore.add_site'
    form_class = SiteForm
    page_title = __("Add site")
    success_message = __("Site '{0}' created.")
    add_url_name = 'wagtailsites:add'
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    template = 'wagtailsites/create.html'
    header_icon = 'site'


class Edit(EditView):
    permission_required = 'wagtailcore.change_site'
    model = Site
    form_class = SiteForm
    success_message = __("Site '{0}' updated.")
    error_message = __("The site could not be saved due to errors.")
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    context_object_name = 'site'
    template = 'wagtailsites/edit.html'


class Delete(DeleteView):
    permission_required = 'wagtailcore.delete_site'
    model = Site
    success_message = __("Site '{0}' deleted.")
    index_url_name = 'wagtailsites:index'
    context_object_name = 'site'
    template = 'wagtailsites/confirm_delete.html'
