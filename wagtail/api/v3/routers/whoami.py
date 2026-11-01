from ninja import Router, Schema

from wagtail.api.v3.auth import BearerTokenAuth

router = Router(tags=["auth"])


class WhoAmIUserSchema(Schema):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    is_superuser: bool


class WhoAmIProfileSchema(Schema):
    avatar_url: str | None


class WhoAmISchema(Schema):
    user: WhoAmIUserSchema
    profile: WhoAmIProfileSchema
    groups: list[str]


@router.get(
    "/whoami/",
    response=WhoAmISchema,
    auth=BearerTokenAuth(),
    url_name="whoami",
    operation_id="whoami",
    summary="Current API user",
)
def whoami(request):
    user = request.user  # set by BearerTokenAuth
    profile = getattr(user, "wagtail_userprofile", None)
    return {
        "user": {
            "id": str(user.pk),
            "username": user.get_username(),
            # Fields may not exist on custom user models.
            "email": getattr(user, "email", "") or "",
            "first_name": getattr(user, "first_name", "") or "",
            "last_name": getattr(user, "last_name", "") or "",
            "is_superuser": bool(getattr(user, "is_superuser", False)),
        },
        "profile": {
            "avatar_url": profile.avatar.url if profile and profile.avatar else None,
        },
        "groups": [group.name for group in user.groups.all()],
    }
