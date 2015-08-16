from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.views.generic.base import View

from wagtail.wagtailcore.models import Site
from wagtail.wagtailsites.forms import SiteForm
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import permission_required, any_permission_required


class Index(View):
    @method_decorator(any_permission_required('wagtailcore.add_site', 'wagtailcore.change_site', 'wagtailcore.delete_site'))
    def get(self, request):
        sites = Site.objects.all()
        return render(request, 'wagtailsites/index.html', {
            'sites': sites,
        })


class Create(View):
    @method_decorator(permission_required('wagtailcore.add_site'))
    def get(self, request):
        self.form = SiteForm()
        return self.render_to_response()

    @method_decorator(permission_required('wagtailcore.add_site'))
    def post(self, request):
        self.form = SiteForm(request.POST)
        if self.form.is_valid():
            site = self.form.save()

            messages.success(request, _("Site '{0}' created.").format(site.hostname), buttons=[
                messages.button(reverse('wagtailsites:edit', args=(site.id,)), _('Edit'))
            ])
            return redirect('wagtailsites:index')
        else:
            return self.render_to_response()

    def render_to_response(self):
        return render(self.request, 'wagtailsites/create.html', {
            'form': self.form,
        })


class Edit(View):
    @method_decorator(permission_required('wagtailcore.change_site'))
    def get(self, request, site_id):
        self.site = get_object_or_404(Site, id=site_id)
        self.form = SiteForm(instance=self.site)
        return self.render_to_response()

    @method_decorator(permission_required('wagtailcore.change_site'))
    def post(self, request, site_id):
        self.site = get_object_or_404(Site, id=site_id)
        self.form = SiteForm(request.POST, instance=self.site)
        if self.form.is_valid():
            site = self.form.save()
            messages.success(request, _("Site '{0}' updated.").format(site.hostname), buttons=[
                messages.button(reverse('wagtailsites:edit', args=(site.id,)), _('Edit'))
            ])
            return redirect('wagtailsites:index')
        else:
            messages.error(request, _("The site could not be saved due to errors."))

        return self.render_to_response()

    def render_to_response(self):
        return render(self.request, 'wagtailsites/edit.html', {
            'site': self.site,
            'form': self.form,
        })


@permission_required('wagtailcore.delete_site')
def delete(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if request.method == 'POST':
        site.delete()
        messages.success(request, _("Site '{0}' deleted.").format(site.hostname))
        return redirect('wagtailsites:index')

    return render(request, "wagtailsites/confirm_delete.html", {
        'site': site,
    })
