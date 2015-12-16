from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers
from django.core.urlresolvers import reverse

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required, any_permission_required
from wagtail.wagtailadmin import messages

from wagtail.wagtailredirects import models
from wagtail.wagtailredirects.forms import RedirectForm


@any_permission_required(
    'wagtailredirects.add_redirect',
    'wagtailredirects.change_redirect',
    'wagtailredirects.delete_redirect'
)
@vary_on_headers('X-Requested-With')
def index(request):
    query_string = request.GET.get('q', "")
    ordering = request.GET.get('ordering', 'old_path')

    redirects = models.Redirect.objects.prefetch_related('redirect_page', 'site')

    # Search
    if query_string:
        redirects = redirects.filter(old_path__icontains=query_string)

    # Ordering (A bit useless at the moment as only 'old_path' is allowed)
    if ordering not in ['old_path']:
        ordering = 'old_path'

    if ordering != 'old_path':
        redirects = redirects.order_by(ordering)

    # Pagination
    paginator, redirects = paginate(request, redirects)

    # Render template
    if request.is_ajax():
        return render(request, "wagtailredirects/results.html", {
            'ordering': ordering,
            'redirects': redirects,
            'query_string': query_string,
        })
    else:
        return render(request, "wagtailredirects/index.html", {
            'ordering': ordering,
            'redirects': redirects,
            'query_string': query_string,
            'search_form': SearchForm(
                data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")
            ),
        })


@permission_required('wagtailredirects.change_redirect')
def edit(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if request.POST:
        form = RedirectForm(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            form.save()
            messages.success(request, _("Redirect '{0}' updated.").format(theredirect.title), buttons=[
                messages.button(reverse('wagtailredirects:edit', args=(theredirect.id,)), _('Edit'))
            ])
            return redirect('wagtailredirects:index')
        else:
            messages.error(request, _("The redirect could not be saved due to errors."))
    else:
        form = RedirectForm(instance=theredirect)

    return render(request, "wagtailredirects/edit.html", {
        'redirect': theredirect,
        'form': form,
    })


@permission_required('wagtailredirects.delete_redirect')
def delete(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if request.POST:
        theredirect.delete()
        messages.success(request, _("Redirect '{0}' deleted.").format(theredirect.title))
        return redirect('wagtailredirects:index')

    return render(request, "wagtailredirects/confirm_delete.html", {
        'redirect': theredirect,
    })


@permission_required('wagtailredirects.add_redirect')
def add(request):
    if request.POST:
        form = RedirectForm(request.POST, request.FILES)
        if form.is_valid():
            theredirect = form.save()

            messages.success(request, _("Redirect '{0}' added.").format(theredirect.title), buttons=[
                messages.button(reverse('wagtailredirects:edit', args=(theredirect.id,)), _('Edit'))
            ])
            return redirect('wagtailredirects:index')
        else:
            messages.error(request, _("The redirect could not be created due to errors."))
    else:
        form = RedirectForm()

    return render(request, "wagtailredirects/add.html", {
        'form': form,
    })
