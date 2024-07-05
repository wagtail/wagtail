from django.apps import apps
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from wagtail.admin.models import EditingSession
from wagtail.admin.utils import get_user_display_name
from wagtail.models import Page, Revision, RevisionMixin
from wagtail.permissions import page_permission_policy


@require_POST
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
    session.is_editing = request.POST.get("is_editing", False)
    try:
        session.full_clean()
    except ValidationError:
        return JsonResponse({"error": "Invalid data"}, status=400)
    else:
        session.save()

    other_sessions = (
        EditingSession.objects.filter(
            content_type=content_type,
            object_id=unquoted_object_id,
            last_seen_at__gte=timezone.now() - timezone.timedelta(minutes=1),
        )
        .exclude(id=session.id)
        .select_related("user")
        .order_by("-last_seen_at")
    )

    # create a lookup of sessions indexed by user ID. Multiple sessions from the same user
    # are merged, such that the most recently seen one is reported, but is_editing is true
    # if any session has the editing flag set (not just the latest one).
    other_sessions_lookup = {}
    for other_session in other_sessions:
        try:
            other_session_info = other_sessions_lookup[other_session.user.pk]
        except KeyError:
            other_sessions_lookup[other_session.user.pk] = {
                "session_id": other_session.id,
                "user": other_session.user,
                "last_seen_at": other_session.last_seen_at,
                "is_editing": other_session.is_editing,
                "revision_id": None,
            }
        else:
            if other_session.is_editing:
                other_session_info["is_editing"] = True

    revision_id = request.POST.get("revision_id", None)
    if revision_id is not None and issubclass(model, RevisionMixin):
        all_revisions = obj.revisions.defer("content")
        try:
            original_revision = all_revisions.get(id=revision_id)
        except Revision.DoesNotExist:
            raise Http404

        newest_revision = (
            all_revisions.filter(created_at__gt=original_revision.created_at)
            .order_by("-created_at", "-pk")
            .select_related("user")
            .first()
        )

        if newest_revision and newest_revision.id != revision_id:
            try:
                session_info = other_sessions_lookup[newest_revision.user_id]
            except KeyError:
                other_sessions_lookup[newest_revision.user_id] = {
                    "session_id": None,
                    "user": newest_revision.user,
                    "last_seen_at": newest_revision.created_at,
                    "is_editing": False,
                    "revision_id": newest_revision.id,
                }
            else:
                session_info["revision_id"] = newest_revision.id
                if newest_revision.created_at > session_info["last_seen_at"]:
                    session_info["last_seen_at"] = newest_revision.created_at

    try:
        users_other_session = other_sessions_lookup[request.user.pk]
    except KeyError:
        pass
    else:
        # If the user has a different session that is not editing and hasn't
        # created the latest revision, hide it as it's not relevant.
        if (
            not users_other_session["is_editing"]
            and not users_other_session["revision_id"]
        ):
            other_sessions_lookup.pop(request.user.pk)

    # Sort the other sessions so that they are presented in the following order:
    # 1. Prioritise any session with the latest revision. Then,
    # 2. Prioritise any session that is currently editing. Then,
    # 3. Prioritise any session with the smallest id, so that new sessions are
    #    appended to the end of the list (they're shown last). We are not sorting
    #    by last_seen_at to avoid shifting the order of the sessions as they
    #    ping the server.
    other_sessions = sorted(
        other_sessions_lookup.values(),
        key=lambda other_session: other_session["session_id"] or 0,
    )
    other_sessions = sorted(
        other_sessions,
        key=lambda other_session: other_session["is_editing"],
        reverse=True,
    )
    other_sessions = sorted(
        other_sessions,
        key=lambda other_session: other_session["revision_id"] or 0,
        reverse=True,
    )

    return JsonResponse(
        {
            "session_id": session.id,
            "other_sessions": [
                {
                    "session_id": other_session["session_id"],
                    "user": get_user_display_name(other_session["user"]),
                    "last_seen_at": other_session["last_seen_at"].isoformat(),
                    "is_editing": other_session["is_editing"],
                    "revision_id": other_session["revision_id"],
                }
                for other_session in other_sessions
            ],
        }
    )


@require_POST
def release(request, session_id):
    EditingSession.objects.filter(id=session_id, user=request.user).delete()
    return JsonResponse({})
