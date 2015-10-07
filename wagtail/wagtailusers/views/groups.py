from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required, any_permission_required
from wagtail.wagtailusers.forms import GroupForm, GroupPagePermissionFormSet, GroupCollectionPermissionFormSet


@any_permission_required('auth.add_group', 'auth.change_group', 'auth.delete_group')
@vary_on_headers('X-Requested-With')
def index(request):
    q = None
    p = request.GET.get("p", 1)
    is_searching = False

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search groups"))
        if form.is_valid():
            q = form.cleaned_data['q']

            is_searching = True
            groups = Group.objects.filter(name__icontains=q)
    else:
        form = SearchForm(placeholder=_("Search groups"))

    if not is_searching:
        groups = Group.objects

    groups = groups.order_by('name')

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering in ['name', 'username']:
            if ordering != 'name':
                groups = groups.order_by(ordering)
    else:
        ordering = 'name'

    paginator = Paginator(groups, 20)

    try:
        groups = paginator.page(p)
    except PageNotAnInteger:
        groups = paginator.page(1)
    except EmptyPage:
        groups = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(request, "wagtailusers/groups/results.html", {
            'groups': groups,
            'is_searching': is_searching,
            'query_string': q,
            'ordering': ordering,
        })
    else:
        return render(request, "wagtailusers/groups/index.html", {
            'search_form': form,
            'groups': groups,
            'is_searching': is_searching,
            'ordering': ordering,
            'query_string': q,
        })


@permission_required('auth.add_group')
def create(request):
    if request.POST:
        form = GroupForm(request.POST)
        page_permission_formset = GroupPagePermissionFormSet(request.POST)
        collection_permission_formset = GroupCollectionPermissionFormSet(request.POST)
        if form.is_valid() and page_permission_formset.is_valid() and collection_permission_formset.is_valid():
            group = form.save()

            page_permission_formset.instance = group
            page_permission_formset.save()

            collection_permission_formset.instance = group
            collection_permission_formset.save()

            messages.success(request, _("Group '{0}' created.").format(group), buttons=[
                messages.button(reverse('wagtailusers_groups:edit', args=(group.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_groups:index')
        else:
            messages.error(request, _("The group could not be created due to errors."))
    else:
        form = GroupForm()
        page_permission_formset = GroupPagePermissionFormSet()
        collection_permission_formset = GroupCollectionPermissionFormSet()

    return render(request, 'wagtailusers/groups/create.html', {
        'form': form,
        'page_permission_formset': page_permission_formset,
        'collection_permission_formset': collection_permission_formset,
    })


@permission_required('auth.change_group')
def edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.POST:
        form = GroupForm(request.POST, instance=group)
        page_permission_formset = GroupPagePermissionFormSet(request.POST, instance=group)
        collection_permission_formset = GroupCollectionPermissionFormSet(request.POST, instance=group)
        if form.is_valid() and page_permission_formset.is_valid() and collection_permission_formset.is_valid():
            group = form.save()
            page_permission_formset.save()
            collection_permission_formset.save()
            messages.success(request, _("Group '{0}' updated.").format(group), buttons=[
                messages.button(reverse('wagtailusers_groups:edit', args=(group.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_groups:index')
        else:
            messages.error(request, _("The group could not be saved due to errors."))
    else:
        form = GroupForm(instance=group)
        page_permission_formset = GroupPagePermissionFormSet(instance=group)
        collection_permission_formset = GroupCollectionPermissionFormSet(instance=group)

    return render(request, 'wagtailusers/groups/edit.html', {
        'group': group,
        'form': form,
        'page_permission_formset': page_permission_formset,
        'collection_permission_formset': collection_permission_formset,
    })


@permission_required('auth.delete_group')
def delete(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.POST:
        group.delete()
        messages.success(request, _("Group '{0}' deleted.").format(group.name))
        return redirect('wagtailusers_groups:index')

    return render(request, "wagtailusers/groups/confirm_delete.html", {
        'group': group,
    })
