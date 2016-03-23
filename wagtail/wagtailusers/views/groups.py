from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.utils.pagination import paginate
from wagtail.wagtailcore import hooks
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required, any_permission_required
from wagtail.wagtailusers.forms import GroupForm, GroupPagePermissionFormSet


_permission_panel_classes = None


def get_permission_panel_classes():
    global _permission_panel_classes
    if _permission_panel_classes is None:
        _permission_panel_classes = [GroupPagePermissionFormSet]
        for fn in hooks.get_hooks('register_group_permission_panel'):
            _permission_panel_classes.append(fn())

    return _permission_panel_classes


@any_permission_required('auth.add_group', 'auth.change_group', 'auth.delete_group')
@vary_on_headers('X-Requested-With')
def index(request):
    q = None
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

    paginator, groups = paginate(request, groups)

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
    group = Group()
    if request.POST:
        form = GroupForm(request.POST, instance=group)
        permission_panels = [
            cls(request.POST, instance=group)
            for cls in get_permission_panel_classes()
        ]
        if form.is_valid() and all(panel.is_valid() for panel in permission_panels):
            form.save()

            for panel in permission_panels:
                panel.save()

            messages.success(request, _("Group '{0}' created.").format(group), buttons=[
                messages.button(reverse('wagtailusers_groups:edit', args=(group.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_groups:index')
        else:
            messages.error(request, _("The group could not be created due to errors."))
    else:
        form = GroupForm(instance=group)
        permission_panels = [
            cls(instance=group)
            for cls in get_permission_panel_classes()
        ]

    return render(request, 'wagtailusers/groups/create.html', {
        'form': form,
        'permission_panels': permission_panels,
    })


@permission_required('auth.change_group')
def edit(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    if request.POST:
        form = GroupForm(request.POST, instance=group)
        permission_panels = [
            cls(request.POST, instance=group)
            for cls in get_permission_panel_classes()
        ]
        if form.is_valid() and all(panel.is_valid() for panel in permission_panels):
            form.save()

            for panel in permission_panels:
                panel.save()

            messages.success(request, _("Group '{0}' updated.").format(group), buttons=[
                messages.button(reverse('wagtailusers_groups:edit', args=(group.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_groups:index')
        else:
            messages.error(request, _("The group could not be saved due to errors."))
    else:
        form = GroupForm(instance=group)
        permission_panels = [
            cls(instance=group)
            for cls in get_permission_panel_classes()
        ]

    return render(request, 'wagtailusers/groups/edit.html', {
        'group': group,
        'form': form,
        'permission_panels': permission_panels,
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
