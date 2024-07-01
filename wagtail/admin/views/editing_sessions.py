from django.apps import apps
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from wagtail.admin.models import EditingSession
from wagtail.models import Page
from wagtail.permissions import page_permission_policy


def ping(request, app_label, model_name, object_id, session_id):
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        raise Http404

    unquoted_object_id = unquote(object_id)

    content_type = ContentType.objects.get_for_model(model)

    obj = get_object_or_404(model, pk=unquoted_object_id)
    if isinstance(obj, Page):
        permission_policy = page_permission_policy
    else:
        try:
            permission_policy = model.snippet_viewset.permission_policy
        except AttributeError:
            # model is neither a Page nor a snippet
            raise Http404

    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", obj
    ):
        raise Http404

    try:
        session = EditingSession.objects.get(
            id=session_id,
            user=request.user,
            content_type=content_type,
            object_id=unquoted_object_id,
        )
    except EditingSession.DoesNotExist:
        session = EditingSession(
            content_type=content_type,
            object_id=unquoted_object_id,
            user=request.user,
        )

    session.last_seen_at = timezone.now()
    session.save()

    return JsonResponse(
        {
            "session_id": session.id,
        }
    )
