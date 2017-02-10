from __future__ import absolute_import, unicode_literals

from django.utils.translation import ugettext_lazy

from wagtail.wagtailadmin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.wagtailcore.models import Site
from wagtail.wagtailcore.permissions import site_permission_policy
from wagtail.wagtailsites.forms import SiteForm


class Index(IndexView):
    permission_policy = site_permission_policy
    model = Site
    context_object_name = 'sites'
    template_name = 'wagtailsites/index.html'
    add_url_name = 'wagtailsites:add'
    page_title = ugettext_lazy("Sites")
    add_item_label = ugettext_lazy("Add a site")
    header_icon = 'site'


class Create(CreateView):
    permission_policy = site_permission_policy
    form_class = SiteForm
    page_title = ugettext_lazy("Add site")
    success_message = ugettext_lazy("Site '{0}' created.")
    add_url_name = 'wagtailsites:add'
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    template_name = 'wagtailsites/create.html'
    header_icon = 'site'


class Edit(EditView):
    permission_policy = site_permission_policy
    model = Site
    form_class = SiteForm
    success_message = ugettext_lazy("Site '{0}' updated.")
    error_message = ugettext_lazy("The site could not be saved due to errors.")
    delete_item_label = ugettext_lazy("Delete site")
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    delete_url_name = 'wagtailsites:delete'
    context_object_name = 'site'
    template_name = 'wagtailsites/edit.html'
    header_icon = 'site'


class Delete(DeleteView):
    permission_policy = site_permission_policy
    model = Site
    success_message = ugettext_lazy("Site '{0}' deleted.")
    index_url_name = 'wagtailsites:index'
    delete_url_name = 'wagtailsites:delete'
    page_title = ugettext_lazy("Delete site")
    confirmation_message = ugettext_lazy("Are you sure you want to delete this site?")
    header_icon = 'site'
