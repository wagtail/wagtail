from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.db.models import Q
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailusers.forms import UserCreationForm, UserEditForm

User = get_user_model()

@permission_required('auth.change_user')
def index(request):
    q = None
    p = request.GET.get("p", 1)
    is_searching = False

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data['q']

            is_searching = True
            users = User.objects.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        users = User.objects

    users = users.order_by('last_name', 'first_name')

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering in ['name', 'username']:
            if ordering != 'name':
                users = users.order_by(ordering)
    else:
        ordering = 'name'

    paginator = Paginator(users, 20)

    try:
        users = paginator.page(p)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    if request.is_ajax():
        return render(request, "wagtailusers/results.html", {
            'users': users,
            'is_searching': is_searching,
            'search_query': q,
            'ordering': ordering,
        })
    else:
        return render(request, "wagtailusers/index.html", {
            'search_form': form,
            'users': users,
            'is_searching': is_searching,
            'ordering': ordering,
            'search_query': q,
        })

@permission_required('auth.change_user')
def create(request):
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' created.").format(user))
            return redirect('wagtailusers_index')
        else:
            messages.error(request, _("The user could not be created due to errors.") )
    else:
        form = UserCreationForm()

    return render(request, 'wagtailusers/create.html', {
        'form': form,
    })


@permission_required('auth.change_user')
def edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.POST:
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' updated.").format(user))
            return redirect('wagtailusers_index')
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = UserEditForm(instance=user)

    return render(request, 'wagtailusers/edit.html', {
        'user': user,
        'form': form,
    })
