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


@permission_required('wagtailcore.add_site')
def create(request):
    if request.method == 'POST':
        form = SiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            messages.success(request, _("Site '{0}' created.").format(site.hostname), buttons=[
                messages.button(reverse('wagtailsites:edit', args=(site.id,)), _('Edit'))
            ])
            return redirect('wagtailsites:index')
        else:
            messages.error(request, _("The site could not be created due to errors."))
    else:
        form = SiteForm()

    return render(request, 'wagtailsites/create.html', {
        'form': form,
    })


@permission_required('wagtailcore.change_site')
def edit(request, site_id):
    site = get_object_or_404(Site, id=site_id)

    if request.method == 'POST':
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            site = form.save()
            messages.success(request, _("Site '{0}' updated.").format(site.hostname), buttons=[
                messages.button(reverse('wagtailsites:edit', args=(site.id,)), _('Edit'))
            ])
            return redirect('wagtailsites:index')
        else:
            messages.error(request, _("The site could not be saved due to errors."))
    else:
        form = SiteForm(instance=site)

    return render(request, 'wagtailsites/edit.html', {
        'site': site,
        'form': form,
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
