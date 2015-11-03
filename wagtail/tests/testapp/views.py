from django.http import HttpResponse

from wagtail.wagtailadmin.utils import user_passes_test


def user_is_called_bob(user):
    return user.first_name == 'Bob'


@user_passes_test(user_is_called_bob)
def bob_only_zone(request):
    return HttpResponse("Bobs of the world unite!")
