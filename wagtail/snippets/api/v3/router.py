from typing import Any, Callable, Literal, cast

from django.conf import settings
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db.models import Model
from django.http import Http404, HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Body, Query, Router, Schema, Status
from ninja.pagination import paginate
from pydantic import PositiveInt

from wagtail.actions import action_registry
from wagtail.actions.publish_revision import PublishPermissionError
from wagtail.api.rich_text import RichTextOutputFormat
from wagtail.api.v3.auth import BearerTokenAuth
from wagtail.api.v3.form_data import build_model_form, build_model_update_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.registry import registry
from wagtail.api.v3.schemas.base import build_discriminated_union, build_union_schemas
from wagtail.api.v3.schemas.params import (
    APIFieldFilterSchema,
    OrderingSchema,
    RevisionFilterSchema,
    SearchSchema,
    TranslationFilterSchema,
)
from wagtail.api.v3.schemas.revisions import RevisionDetailSchema, RevisionSchema
from wagtail.coreutils import resolve_model_string
from wagtail.models import DraftStateMixin, Locale, RevisionMixin, TranslatableMixin
from wagtail.permissions import policy_registry
from wagtail.snippets.api.v3.schemas import ParamTypeInjectingBody
from wagtail.snippets.models import get_snippet_models

router = Router(tags=["snippets"], auth=BearerTokenAuth())
actions_router = Router(auth=BearerTokenAuth())

enabled_models = [
    model for model in get_snippet_models() if registry.has(model._meta.label)
]


def _type_literal(models):
    # A Literal[] of no options isn't valid, so fall back to a type/schema
    # that can never match a real request when no snippet model has the
    # relevant mixin - the router still imports (and the OpenAPI schema
    # still generates) with nothing to build a union from.
    if not models:
        return Literal[""]
    return Literal[tuple(model._meta.label for model in models)]  # ty: ignore[invalid-type-form]


SnippetTypeLiteral = _type_literal(enabled_models)

if enabled_models:
    _snippet_schemas = build_union_schemas(enabled_models)
    SnippetDetailSchema = _snippet_schemas.detail
    SnippetCreateSchema = _snippet_schemas.create
    SnippetUpdateSchema = _snippet_schemas.update
else:
    # No snippet models are registered - fall back to a type/schema that can
    # never match a real request, so the router still imports (and the
    # OpenAPI schema still generates) with no snippet models to build a
    # union from.
    class _NoSnippetModelsSchema(Schema):
        meta: Any = None

    SnippetDetailSchema = SnippetCreateSchema = SnippetUpdateSchema = (
        _NoSnippetModelsSchema
    )

mixins = (RevisionMixin, DraftStateMixin, TranslatableMixin)
literals_by_mixin = {}
schemas_by_mixin = {}
for mixin in mixins:
    models = cast(
        list[type[Model]],
        [model for model in enabled_models if issubclass(model, mixin)],
    )
    for_schema = cast(
        Callable[[type[Model]], type[Any]],
        lambda model: (reg := registry.get(model._meta.label)) and reg.read_schema,
    )
    literals_by_mixin[mixin] = _type_literal(models)
    if models:
        schemas_by_mixin[mixin] = build_discriminated_union(models, for_schema)
    else:
        schemas_by_mixin[mixin] = SnippetDetailSchema


def get_model_from_params(request, *args, type: SnippetTypeLiteral, **kwargs):
    return resolve_model_string(type)


def _check_can_view_revisions(request: HttpRequest, instance) -> None:
    permission_policy = policy_registry.get(instance)
    if not permission_policy.user_has_permission_for_instance(
        request.user, "change", instance
    ):
        raise PermissionDenied


class SnippetRevisionDetailSchema(RevisionDetailSchema):
    content_object: schemas_by_mixin[RevisionMixin]  # ty: ignore[invalid-type-form]

    @staticmethod
    def resolve_content_object(obj):
        return obj.as_object()


@router.get(
    "/{type}/",
    response=list[SnippetDetailSchema],
    url_name="list_snippets",
    summary="List snippets",
    operation_id="snippets_list",
)
@paginate(
    WagtailLimitOffsetPagination,
    pass_parameter="pagination_info",  # noqa: S106 not a password
)
@require_any_permission(get_model_from_params, ("add", "change", "delete", "view"))
def list_snippets(
    request: HttpRequest,
    type: SnippetTypeLiteral,
    translation_filter: TranslationFilterSchema = Query(...),  # ty: ignore[call-non-callable]
    ordering: OrderingSchema = Query(...),  # ty: ignore[call-non-callable]
    search: SearchSchema = Query(...),  # ty: ignore[call-non-callable]
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
    **kwargs,
):
    pagination_info = cast(
        WagtailLimitOffsetPagination.Input,
        kwargs.get("pagination_info"),
    )
    model = resolve_model_string(type)
    base_fields = [model._meta.pk.name]
    field_filter = APIFieldFilterSchema.with_exclude_schemas(
        raw_params=request.GET,
        schemas=(TranslationFilterSchema, OrderingSchema, SearchSchema),
        base_fields=base_fields,
    )
    permission_policy = policy_registry.get_by_type(model)
    queryset = permission_policy.instances_user_has_any_permission_for(
        request.user, ("add", "change", "delete", "view")
    ).order_by(model._meta.pk.name)
    queryset = translation_filter.filter_queryset(queryset)
    queryset = field_filter.filter_queryset(queryset)
    queryset = ordering.order_queryset(
        queryset, pagination_info, base_fields=base_fields
    )
    queryset = search.search_queryset(request, queryset)
    return queryset


@router.get(
    "/{type}/{pk}/",
    response=SnippetDetailSchema,
    url_name="detail_snippet",
    summary="Snippet detail",
    operation_id="snippets_detail",
)
@require_any_permission(get_model_from_params, ("add", "change", "delete", "view"))
def get_snippet(
    request: HttpRequest,
    type: SnippetTypeLiteral,
    pk: str,
    version: Literal["live", "draft"] = Query("live"),  # ty: ignore[call-non-callable]
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(type)
    permission_policy = policy_registry.get_by_type(model)
    instance = get_object_or_404(
        permission_policy.instances_user_has_any_permission_for(
            request.user, ("add", "change", "delete", "view")
        ),
        pk=unquote(pk),
    )
    # The router requires authentication, so draft reads are always allowed
    if version == "draft" and issubclass(model, DraftStateMixin):
        return instance.get_latest_revision_as_object()
    return instance


@router.post(
    "/{type}/",
    response={201: SnippetDetailSchema},
    url_name="create_snippet",
    summary="Create snippet",
    operation_id="snippets_create",
)
@require_any_permission(get_model_from_params, ("add",))
def create_snippet(
    request: HttpRequest,
    type: SnippetTypeLiteral,
    data: SnippetCreateSchema = ParamTypeInjectingBody(...),
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(type)
    form = build_model_form(model, data, user=request.user)
    action_class = action_registry.get_action_class(model, "create")
    action = action_class(
        form.instance,
        user=request.user,
        form=form,
        publish=getattr(data.meta, "action", None) == "publish",
    )
    action.execute()
    return Status(201, form.instance)


@router.patch(
    "/{type}/{pk}/",
    response=SnippetDetailSchema,
    url_name="update_snippet",
    summary="Update snippet",
    operation_id="snippets_update",
)
@require_any_permission(get_model_from_params, ("change",))
def update_snippet(
    request: HttpRequest,
    type: SnippetTypeLiteral,
    pk: str,
    data: SnippetUpdateSchema = ParamTypeInjectingBody(...),
    rich_text_format: RichTextOutputFormat | None = Query(None),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    form = build_model_update_form(instance, data, user=request.user)
    action_class = action_registry.get_action_class(model, "edit")
    action = action_class(
        form.instance,
        user=request.user,
        form=form,
        publish=getattr(data.meta, "action", None) == "publish",
    )
    action.execute()
    return form.instance


@router.delete(
    "/{type}/{pk}/",
    response={204: None},
    url_name="delete_snippet",
    summary="Delete snippet",
    operation_id="snippets_delete",
)
@actions_router.delete(
    "/{type}/{pk}/actions/delete/",
    response={204: None},
    url_name="snippets_actions_delete",
    summary="Delete snippet",
    operation_id="snippets_actions_delete",
)
@require_any_permission(get_model_from_params, ("delete",))
def delete_snippet(request: HttpRequest, type: SnippetTypeLiteral, pk: str):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    action_class = action_registry.get_action_class(model, "delete")
    action = action_class(instance, user=request.user)
    action.execute()
    return Status(204, None)


@router.get(
    "/{type}/{pk}/revisions/",
    response=list[RevisionSchema],
    url_name="list_snippet_revisions",
    summary="List snippet revisions",
    operation_id="snippets_revisions_list",
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(get_model_from_params, ("add", "change", "delete"))
def list_snippet_revisions(
    request: HttpRequest,
    type: literals_by_mixin[RevisionMixin],  # ty: ignore[invalid-type-form]
    pk: str,
    filters: RevisionFilterSchema = Query(...),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    _check_can_view_revisions(request, instance)
    queryset = instance.revisions.order_by("-created_at", "-id")
    return filters.filter(queryset)


@router.get(
    "/{type}/{pk}/revisions/{revision_id}/",
    response=SnippetRevisionDetailSchema,
    url_name="detail_snippet_revision",
    summary="Snippet revision detail",
    operation_id="snippets_revisions_detail",
)
@require_any_permission(get_model_from_params, ("add", "change", "delete"))
def get_snippet_revision(
    request: HttpRequest,
    type: literals_by_mixin[RevisionMixin],  # ty: ignore[invalid-type-form]
    pk: str,
    revision_id: PositiveInt,
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    _check_can_view_revisions(request, instance)
    revisions = instance.revisions.select_related("content_type", "base_content_type")
    return get_object_or_404(revisions, pk=revision_id)


@actions_router.post(
    "/{type}/{pk}/actions/publish/",
    response=(schemas_by_mixin[DraftStateMixin]),
    url_name="snippets_actions_publish",
    summary="Publish snippet",
    operation_id="snippets_actions_publish",
)
def publish_snippet(
    request: HttpRequest,
    type: literals_by_mixin[DraftStateMixin],  # ty: ignore[invalid-type-form]
    pk: str,
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    revision = instance.get_latest_revision()

    # If the object has no revision, create one only if the user has
    # permission - matching the equivalent check in the pages router.
    if revision is None:
        permission_policy = policy_registry.get(instance)
        if not permission_policy.user_has_permission_for_instance(
            request.user, "publish", instance
        ):
            raise PublishPermissionError(
                "You do not have permission to publish this object."
            )
        revision = instance.save_revision(user=request.user)

    action_class = action_registry.get_action_class(model, "publish")
    action = action_class(revision, user=request.user)
    action.execute()
    return model.objects.get(pk=instance.pk)


@actions_router.post(
    "/{type}/{pk}/actions/unpublish/",
    response=(schemas_by_mixin[DraftStateMixin]),
    url_name="snippets_actions_unpublish",
    summary="Unpublish snippet",
    operation_id="snippets_actions_unpublish",
)
def unpublish_snippet(
    request: HttpRequest,
    type: literals_by_mixin[DraftStateMixin],  # ty: ignore[invalid-type-form]
    pk: str,
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    action_class = action_registry.get_action_class(model, "unpublish")
    action = action_class(instance, user=request.user)
    action.execute()
    return instance


class SnippetRevertSchema(Schema):
    revision_id: PositiveInt


@actions_router.post(
    "/{type}/{pk}/actions/revert/",
    response=(schemas_by_mixin[RevisionMixin]),
    url_name="snippets_actions_revert",
    summary="Revert snippet to a previous revision",
    operation_id="snippets_actions_revert",
)
def revert_snippet(
    request: HttpRequest,
    type: literals_by_mixin[RevisionMixin],  # ty: ignore[invalid-type-form]
    pk: str,
    data: SnippetRevertSchema = Body(...),  # ty: ignore[call-non-callable]
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    revision = get_object_or_404(instance.revisions, id=data.revision_id)
    action_class = action_registry.get_action_class(model, "revert")
    action = action_class(instance=instance, revision=revision, user=request.user)
    new_revision = action.execute()
    return new_revision.as_object()


class SnippetCopyForTranslationSchema(Schema):
    locale: str


@actions_router.post(
    "/{type}/{pk}/actions/copy_for_translation/",
    response={201: schemas_by_mixin[TranslatableMixin]},
    url_name="snippets_actions_copy_for_translation",
    summary="Copy snippet for translation",
    operation_id="snippets_actions_copy_for_translation",
)
def copy_for_translation(
    request: HttpRequest,
    type: literals_by_mixin[TranslatableMixin],  # ty: ignore[invalid-type-form]
    pk: str,
    data: SnippetCopyForTranslationSchema = Body(...),  # ty: ignore[call-non-callable]
):
    if not getattr(settings, "WAGTAIL_I18N_ENABLED", False):
        raise Http404("Internationalization is not enabled.")

    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=unquote(pk))
    locale = get_object_or_404(Locale, language_code=data.locale)

    action_class = action_registry.get_action_class(model, "copy_for_translation")
    action = action_class(instance, locale, user=request.user)
    new_instance = action.execute()
    new_instance.save()
    return Status(201, new_instance)


router.add_router("/", actions_router)
