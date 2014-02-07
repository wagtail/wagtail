from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages

from wagtail.wagtailusers.forms import UserCreationForm, UserEditForm


@permission_required('auth.change_user')
def index(request):
    p = request.GET.get("p", 1)

    users = User.objects.order_by('last_name', 'first_name')

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

    return render(request, 'wagtailusers/index.html', {
        'users': users,
        'ordering': ordering,
    })


@permission_required('auth.change_user')
def create(request):
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "User '%s' created." % user)
            return redirect('wagtailusers_index')
        else:
            messages.error(request, "The user could not be created due to errors.")
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
            messages.success(request, "User '%s' updated." % user)
            return redirect('wagtailusers_index')
        else:
            messages.error(request, "The user could not be saved due to errors.")
    else:
        form = UserEditForm(instance=user)

    return render(request, 'wagtailusers/edit.html', {
        'user': user,
        'form': form,
    })
