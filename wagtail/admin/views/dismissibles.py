import json

from django.http import HttpResponseBadRequest, JsonResponse
from django.views import View

from wagtail.users.models import UserProfile


class DismissiblesView(View):
    def get(self, request, *args, **kwargs):
        # The UserProfile may not exist for the user, in which case return an empty object
        profile = getattr(request.user, "wagtail_userprofile", None)
        dismissibles = profile.dismissibles if profile else {}
        return JsonResponse(dismissibles)

    def patch(self, request, *args, **kwargs):
        try:
            updates = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponseBadRequest()

        # Make sure the UserProfile exists
        profile = UserProfile.get_for_user(request.user)
        profile.dismissibles.update(updates)
        profile.save(update_fields=["dismissibles"])
        return JsonResponse(profile.dismissibles)
