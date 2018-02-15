from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.forms import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker, permission_denied
from wagtail.contrib.redirects import models
from wagtail.contrib.redirects.forms import RedirectForm
from wagtail.contrib.redirects.permissions import permission_policy
from wagtail.utils.pagination import paginate

permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    query_string = request.GET.get('q', "")
    ordering = request.GET.get('ordering', 'old_path')

    redirects = models.Redirect.objects.prefetch_related('redirect_page', 'site')

    # Search
    if query_string:
        redirects = redirects.filter(Q(old_path__icontains=query_string) |
                                     Q(redirect_page__url_path__icontains=query_string) |
                                     Q(redirect_link__icontains=query_string))

    # Ordering (A bit useless at the moment as only 'old_path' is allowed)
    if ordering not in ['old_path']:
        ordering = 'old_path'

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
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('change')
def edit(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, 'change', theredirect
    ):
        return permission_denied(request)

    if request.method == 'POST':
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
        'user_can_delete': permission_policy.user_has_permission(request.user, 'delete'),
    })


@permission_checker.require('delete')
def delete(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, 'delete', theredirect
    ):
        return permission_denied(request)

    if request.method == 'POST':
        theredirect.delete()
        messages.success(request, _("Redirect '{0}' deleted.").format(theredirect.title))
        return redirect('wagtailredirects:index')

    return render(request, "wagtailredirects/confirm_delete.html", {
        'redirect': theredirect,
    })


@permission_checker.require('add')
def add(request):
    if request.method == 'POST':
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
