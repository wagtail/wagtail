from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _, ugettext_lazy as __

from wagtail.wagtailcore.models import Site
from wagtail.wagtailsites.forms import SiteForm
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.views.generic import PermissionCheckedView, IndexView, CreateView, EditView


class Index(IndexView):
    any_permission_required = ['wagtailcore.add_site', 'wagtailcore.change_site', 'wagtailcore.delete_site']
    model = Site
    context_object_name = 'sites'
    template = 'wagtailsites/index.html'


class Create(CreateView):
    permission_required = 'wagtailcore.add_site'
    form_class = SiteForm
    success_message = __("Site '{0}' created.")
    edit_url_name = 'wagtailsites:edit'
    index_url_name = 'wagtailsites:index'
    template = 'wagtailsites/create.html'


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


class Delete(PermissionCheckedView):
    permission_required = 'wagtailcore.delete_site'

    def get(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        return render(request, "wagtailsites/confirm_delete.html", {
            'site': site,
        })

    def post(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        site.delete()
        messages.success(request, _("Site '{0}' deleted.").format(site.hostname))
        return redirect('wagtailsites:index')
