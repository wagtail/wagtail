import json
import random
from collections import namedtuple

from django.contrib.auth import get_user_model
from django.http import HttpResponseBadRequest, JsonResponse
from django.http.response import HttpResponse as HttpResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from wagtail.users.models import UserProfile

EditingSession = namedtuple(
    "EditingSession", ["content_object", "user", "last_seen_at", "state"]
)


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


class ActiveSessionsView(TemplateView):
    template_name = "wagtailadmin/shared/headers/_active_sessions.html"

    def get_active_sessions(self):
        User = get_user_model()
        sessions = [
            EditingSession(user, user, timezone.now(), idx)
            for idx, user in enumerate(
                User.objects.all().select_related("wagtail_userprofile")
            )
        ]
        random.shuffle(sessions)
        sessions = sessions[random.randint(0, len(sessions) - 1) :]
        sessions = [
            EditingSession(session.user, session.user, session.last_seen_at, idx)
            for idx, session in enumerate(sessions)
        ]
        return sessions

    def get_context_data(self, **kwargs):
        return {"active_sessions": self.get_active_sessions()}


class ReleaseView(View):
    def post(self, request, *args, **kwargs):
        return JsonResponse({"success": True})
