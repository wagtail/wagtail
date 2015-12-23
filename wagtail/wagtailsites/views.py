from django.utils.translation import ugettext_lazy as __

from wagtail.wagtailcore.models import Site
from wagtail.wagtailsites.forms import SiteForm
from wagtail.wagtailadmin.views import generic
from wagtail.wagtailadmin.modules.model import ModelModule


class IndexView(generic.IndexView):
    any_permission_required = ['wagtailcore.add_site', 'wagtailcore.change_site', 'wagtailcore.delete_site']
    context_object_name = 'sites'
    add_permission_name = 'wagtailcore.add_site'
    page_title = __("Sites")
    add_item_label = __("Add a site")


class CreateView(generic.CreateView):
    permission_required = 'wagtailcore.add_site'
    page_title = __("Add site")
    success_message = __("Site '{0}' created.")


class EditView(generic.EditView):
    permission_required = 'wagtailcore.change_site'
    success_message = __("Site '{0}' updated.")
    error_message = __("The site could not be saved due to errors.")
    delete_item_label = __("Delete site")
    delete_permission_name = 'wagtailcore.delete_site'
    context_object_name = 'site'


class DeleteView(generic.DeleteView):
    permission_required = 'wagtailcore.delete_site'
    success_message = __("Site '{0}' deleted.")
    page_title = __("Delete site")
    confirmation_message = __("Are you sure you want to delete this site?")


class SiteModule(ModelModule):
    icon = 'site'
    model = Site

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    def get_form_class(self, for_update=False):
        return SiteForm


module = SiteModule('wagtailsites')
