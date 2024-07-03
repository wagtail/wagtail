from django.apps import apps
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from wagtail.admin.models import EditingSession
from wagtail.admin.utils import get_user_display_name
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
    session.is_editing = request.GET.get("editing", False)
    session.save()

    other_sessions = (
        EditingSession.objects.filter(
            content_type=content_type,
            object_id=unquoted_object_id,
            last_seen_at__gte=timezone.now() - timezone.timedelta(minutes=1),
        )
        .exclude(id=session.id)
        .select_related("user")
    )

    return JsonResponse(
        {
            "session_id": session.id,
            "other_sessions": [
                {
                    "session_id": other_session.id,
                    "user": get_user_display_name(other_session.user),
                    "last_seen_at": other_session.last_seen_at.isoformat(),
                    "is_editing": other_session.is_editing,
                }
                for other_session in other_sessions
            ],
        }
    )


@require_POST
def release(request, session_id):
    EditingSession.objects.filter(id=session_id, user=request.user).delete()
    return JsonResponse({})
