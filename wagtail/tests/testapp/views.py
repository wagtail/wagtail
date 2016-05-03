from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.utils import user_passes_test


def user_is_called_bob(user):
    return user.first_name == 'Bob'


@user_passes_test(user_is_called_bob)
def bob_only_zone(request):
    return HttpResponse("Bobs of the world unite!")


def message_test(request):
    if request.method == 'POST':
        fn = getattr(messages, request.POST['level'])
        fn(request, request.POST['message'])
        return redirect('testapp_message_test')
    else:
        return TemplateResponse(request, 'wagtailadmin/base.html')
