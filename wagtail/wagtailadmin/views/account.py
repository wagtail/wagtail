from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.views import login


def account(request):
    return render(request, 'wagtailadmin/account/account.html', {
        'show_change_password': getattr(settings, 'WAGTAIL_PASSWORD_MANAGEMENT_ENABLED', True) and request.user.has_usable_password(),
    })


def change_password(request):
    can_change_password = request.user.has_usable_password()

    if can_change_password:
        if request.POST:
            form = SetPasswordForm(request.user, request.POST)

            if form.is_valid():
                form.save()

                messages.success(request, "Your password has been changed successfully!")
                return redirect('wagtailadmin_account')
        else:
            form = SetPasswordForm(request.user)
    else:
        form = None

    return render(request, 'wagtailadmin/account/change_password.html', {
        'form': form,
        'can_change_password': can_change_password,
    })

# Wrap login view to prevent logged in users accessing the page
def login_wrapper(request, **kwargs):
    if request.user.is_authenticated():
        return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        return login(request, **kwargs)
        
