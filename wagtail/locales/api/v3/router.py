from django.core.exceptions import ValidationError
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.pagination import paginate
from pydantic import PositiveInt

from wagtail.actions import action_registry
from wagtail.api.v3.auth import BearerTokenAuth
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.schemas import BaseSchema
from wagtail.locales.forms import LocaleForm
from wagtail.locales.utils import get_locale_usage
from wagtail.models import Locale
from wagtail.permissions import policy_registry

router = Router(tags=["locales"], auth=BearerTokenAuth())


class LocaleSchema(BaseSchema):
    id: PositiveInt
    language_code: str
    display_name: str
    is_bidi: bool
    is_default: bool

    @staticmethod
    def resolve_display_name(obj: Locale) -> str:
        return str(obj)


class LocaleInputSchema(Schema):
    language_code: str


def _check_can_delete(locale: Locale):
    if not Locale.all_objects.exclude(pk=locale.pk).exists():
        raise ValidationError(
            "This locale cannot be deleted because there are no other locales."
        )

    if get_locale_usage(locale) != (0, 0):
        raise ValidationError(
            "This locale cannot be deleted because there are pages and/or "
            "other objects using it."
        )


@router.get(
    "/",
    response=list[LocaleSchema],
    url_name="list_locales",
    summary="List locales",
    operation_id="locales_list",
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(Locale)
def list_locales(request: HttpRequest):
    permission_policy = policy_registry.get_by_type(Locale)
    return permission_policy.instances_user_has_any_permission_for(
        request.user,
        ("add", "change", "delete", "view"),
    )


@router.get(
    "/{locale_id}/",
    response=LocaleSchema,
    url_name="detail_locale",
    summary="Locale detail",
    operation_id="locales_detail",
)
@require_any_permission(Locale)
def get_locale_detail(request: HttpRequest, locale_id: int):
    permission_policy = policy_registry.get_by_type(Locale)
    return get_object_or_404(
        permission_policy.instances_user_has_any_permission_for(
            request.user,
            ("add", "change", "delete", "view"),
        ),
        pk=locale_id,
    )


@router.post(
    "/",
    response={201: LocaleSchema},
    url_name="create_locale",
    summary="Create locale",
    operation_id="locales_create",
)
@require_any_permission(Locale, ("add",))
def create_locale(request: HttpRequest, data: LocaleInputSchema):
    form = LocaleForm(data.dict())
    action_class = action_registry.get_action_class(Locale, "create")
    action_class(form.instance, user=request.user, form=form).execute(
        skip_permission_checks=True
    )
    return Status(201, form.instance)


@router.put(
    "/{locale_id}/",
    response=LocaleSchema,
    url_name="update_locale",
    summary="Update locale",
    operation_id="locales_update",
)
@require_any_permission(Locale, ("change",))
def update_locale(request: HttpRequest, locale_id: int, data: LocaleInputSchema):
    locale = get_object_or_404(Locale.all_objects, pk=locale_id)
    form = LocaleForm(data.dict(), instance=locale)
    action_class = action_registry.get_action_class(Locale, "edit")
    action_class(form.instance, user=request.user, form=form).execute()
    return form.instance


@router.delete(
    "/{locale_id}/",
    response={204: None},
    url_name="delete_locale",
    summary="Delete locale",
    operation_id="locales_delete",
)
@require_any_permission(Locale, ("delete",))
def delete_locale(request: HttpRequest, locale_id: int):
    locale = get_object_or_404(Locale.all_objects, pk=locale_id)
    _check_can_delete(locale)
    action_class = action_registry.get_action_class(Locale, "delete")
    action_class(locale, user=request.user).execute()
    return Status(204, None)
