from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.views.decorators.vary import vary_on_headers

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailadmin.utils import permission_required, any_permission_required
from wagtail.wagtailusers.forms import UserCreationForm, UserEditForm
from wagtail.wagtailcore.compat import AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME

User = get_user_model()

# Typically we would check the permission 'auth.change_user' (and 'auth.add_user' /
# 'auth.delete_user') for user management actions, but this may vary according to
# the AUTH_USER_MODEL setting
add_user_perm = "{0}.add_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
change_user_perm = "{0}.change_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())
delete_user_perm = "{0}.delete_{1}".format(AUTH_USER_APP_LABEL, AUTH_USER_MODEL_NAME.lower())


@any_permission_required(add_user_perm, change_user_perm, delete_user_perm)
@vary_on_headers('X-Requested-With')
def index(request):
    q = None
    is_searching = False

    model_fields = [f.name for f in User._meta.get_fields()]

    if 'q' in request.GET:
        form = SearchForm(request.GET, placeholder=_("Search users"))
        if form.is_valid():
            q = form.cleaned_data['q']
            is_searching = True
            conditions = Q()

            if 'username' in model_fields:
                conditions |= Q(username__icontains=q)

            if 'first_name' in model_fields:
                conditions |= Q(first_name__icontains=q)

            if 'last_name' in model_fields:
                conditions |= Q(last_name__icontains=q)

            if 'email' in model_fields:
                conditions |= Q(email__icontains=q)

            users = User.objects.filter(conditions)
    else:
        form = SearchForm(placeholder=_("Search users"))

    if not is_searching:
        users = User.objects.all()

    if 'last_name' in model_fields and 'first_name' in model_fields:
        users = users.order_by('last_name', 'first_name')

    if 'ordering' in request.GET:
        ordering = request.GET['ordering']

        if ordering == 'username':
            users = users.order_by(User.USERNAME_FIELD)
    else:
        ordering = 'name'

    paginator, users = paginate(request, users)

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


@permission_required(add_user_perm)
def create(request):
    if request.POST:
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("User '{0}' created.").format(user), buttons=[
                messages.button(reverse('wagtailusers_users:edit', args=(user.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_users:index')
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
                messages.button(reverse('wagtailusers_users:edit', args=(user.id,)), _('Edit'))
            ])
            return redirect('wagtailusers_users:index')
        else:
            messages.error(request, _("The user could not be saved due to errors."))
    else:
        form = UserEditForm(instance=user)

    return render(request, 'wagtailusers/users/edit.html', {
        'user': user,
        'form': form,
    })
