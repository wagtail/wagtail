from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailusers.forms import UserCreationForm, UserEditForm
from wagtail.wagtailcore.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME

User = get_user_model()

# Typically we would check the permission 'auth.change_user' for user
# management actions, but this may vary according to the AUTH_USER_MODEL
# setting
change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


@permission_required(change_user_perm)
@vary_on_headers('X-Requested-With')
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
        return render(request, "wagtailusers/users/results.html", {
            'users': users,
            'is_searching': is_searching,
            'query_string': q,
            'ordering': ordering,
        })
    else:
        return render(request, "wagtailusers/users/index.html", {
            'search_form': form,
            'users': users,
            'is_searching': is_searching,
            'ordering': ordering,
            'query_string': q,
        })


@permission_required(change_user_perm)
def create(request):
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' created.").format(user), buttons=[
                messages.button(reverse('wagtailusers_users_edit', args=(user.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_users_index')
        else:
            messages.error(request, _("The user could not be created due to errors."))
    else:
        form = UserCreationForm()

    return render(request, 'wagtailusers/users/create.html', {
        'form': form,
    })


@permission_required(change_user_perm)
def edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.POST:
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' updated.").format(user), buttons=[
                messages.button(reverse('wagtailusers_users_edit', args=(user.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_users_index')
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = UserEditForm(instance=user)

    return render(request, 'wagtailusers/users/edit.html', {
        'user': user,
        'form': form,
    })
