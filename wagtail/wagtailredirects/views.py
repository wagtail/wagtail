from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext  as _

from wagtail.wagtailadmin.edit_handlers import ObjectList
from wagtail.wagtailadmin.forms import SearchForm

import models


REDIRECT_EDIT_HANDLER = ObjectList(models.Redirect.content_panels)


@permission_required('wagtailredirects.change_redirect')
def index(request):
    p = request.GET.get("p", 1)
    q = None
    is_searching = False

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search redirects"))
        if form.is_valid():
            q = form.cleaned_data['q']
            is_searching = True

            redirects = models.Redirect.get_for_site(site=request.site).prefetch_related('redirect_page').filter(old_path__icontains=q)

    if not is_searching:
        # Get redirects
        redirects = models.Redirect.get_for_site(site=request.site).prefetch_related('redirect_page')
        form = SearchForm(placeholder=_("Search redirects"))

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering in ['old_path', ]:
            if ordering != 'old_path':
                redirects = redirects.order_by(ordering)
    else:
        ordering = 'old_path'

    paginator = Paginator(redirects, 20)

    try:
        redirects = paginator.page(p)
    except PageNotAnInteger:
        redirects = paginator.page(1)
    except EmptyPage:
        redirects = paginator.page(paginator.num_pages)

    # Render template
    if request.is_ajax():
        return render(request, "wagtailredirects/results.html", {
            'ordering': ordering,
            'redirects': redirects,
            'is_searching': is_searching,
            'search_query': q,
        })
    else:
        return render(request, "wagtailredirects/index.html", {
            'ordering': ordering,
            'search_form': form,
            'redirects': redirects,
            'is_searching': is_searching,
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

            messages.success(request, _("Redirect '{0} added.").format(theredirect.title))
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
