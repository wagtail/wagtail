from django.utils.translation import ugettext_lazy as __

from wagtail.wagtailcore.models import Site
from wagtail.wagtailcore.permissions import site_permission_policy
from wagtail.wagtailsites.forms import SiteForm
from wagtail.wagtailadmin.views.generic import IndexView, CreateView, EditView, DeleteView


class Index(IndexView):
    permission_policy = site_permission_policy
    model = Site
    context_object_name = 'sites'
    template_name = 'wagtailsites/index.html'
    add_url_name = 'wagtailsites:add'
    page_title = __("Sites")
    add_item_label = __("Add a site")
    header_icon = 'site'


class Create(CreateView):
    permission_policy = site_permission_policy
    form_class = SiteForm
    page_title = __("Add site")
    success_message = __("Site '{0}' created.")
    add_url_name = 'wagtailsites:add'
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    template_name = 'wagtailsites/create.html'
    header_icon = 'site'


class Edit(EditView):
    permission_policy = site_permission_policy
    model = Site
    form_class = SiteForm
    success_message = __("Site '{0}' updated.")
    error_message = __("The site could not be saved due to errors.")
    delete_item_label = __("Delete site")
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    delete_url_name = 'wagtailsites:delete'
    context_object_name = 'site'
    template_name = 'wagtailsites/edit.html'
    header_icon = 'site'


class Delete(DeleteView):
    permission_policy = site_permission_policy
    model = Site
    success_message = __("Site '{0}' deleted.")
    index_url_name = 'wagtailsites:index'
    delete_url_name = 'wagtailsites:delete'
    page_title = __("Delete site")
    confirmation_message = __("Are you sure you want to delete this site?")
    header_icon = 'site'
