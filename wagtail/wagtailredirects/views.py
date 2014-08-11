from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext  as _
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin.edit_handlers import ObjectList
from wagtail.wagtailadmin.forms import SearchForm

from wagtail.wagtailredirects import models


REDIRECT_EDIT_HANDLER = ObjectList(models.Redirect.content_panels)


@permission_required('wagtailredirects.change_redirect')
@vary_on_headers('X-Requested-With')
def index(request):
    page = request.GET.get('p', 1)
    query_string = request.GET.get('q', "")
    ordering = request.GET.get('ordering', 'old_path')

    redirects = models.Redirect.get_for_site(site=request.site).prefetch_related('redirect_page')

    # Search
    if query_string:
        redirects = redirects.filter(old_path__icontains=query_string)

    # Ordering (A bit useless at the moment as only 'old_path' is allowed)
    if ordering not in ['old_path']:
        ordering = 'old_path'

    if ordering != 'old_path':
        redirects = redirects.order_by(ordering)

    # Pagination
    paginator = Paginator(redirects, 20)
    try:
        redirects = paginator.page(page)
    except PageNotAnInteger:
        redirects = paginator.page(1)
    except EmptyPage:
        redirects = paginator.page(paginator.num_pages)

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
            'search_form': SearchForm(data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")),
        })


@permission_required('wagtailredirects.change_redirect')
def edit(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    form_class = REDIRECT_EDIT_HANDLER.get_form_class(models.Redirect)
    if request.POST:
        form = form_class(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            form.save()
            messages.success(request, _("Redirect '{0}' updated.").format(theredirect.title))
            return redirect('wagtailredirects_index')
        else:
            messages.error(request, _("The redirect could not be saved due to errors."))
            edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)
    else:
        form = form_class(instance=theredirect)
        edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)

    return render(request, "wagtailredirects/edit.html", {
        'redirect': theredirect,
        'edit_handler': edit_handler,
    })


@permission_required('wagtailredirects.change_redirect')
def delete(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if request.POST:
        theredirect.delete()
        messages.success(request, _("Redirect '{0}' deleted.").format(theredirect.title))
        return redirect('wagtailredirects_index')

    return render(request, "wagtailredirects/confirm_delete.html", {
        'redirect': theredirect,
    })


@permission_required('wagtailredirects.change_redirect')
def add(request):
    theredirect = models.Redirect()

    form_class = REDIRECT_EDIT_HANDLER.get_form_class(models.Redirect)
    if request.POST:
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            theredirect = form.save(commit=False)
            theredirect.site = request.site
            theredirect.save()

            messages.success(request, _("Redirect '{0}' added.").format(theredirect.title))
            return redirect('wagtailredirects_index')
        else:
            messages.error(request, _("The redirect could not be created due to errors."))
            edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)
    else:
        form = form_class()
        edit_handler = REDIRECT_EDIT_HANDLER(instance=theredirect, form=form)

    return render(request, "wagtailredirects/add.html", {
        'edit_handler': edit_handler,
    })
