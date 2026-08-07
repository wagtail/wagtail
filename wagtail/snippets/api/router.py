from typing import Any, Literal

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, Schema, Status
from ninja.pagination import paginate

from wagtail.actions.create import CreateAction
from wagtail.actions.delete import DeleteAction
from wagtail.actions.edit import EditAction
from wagtail.api.v3.form_data import build_model_form, build_model_update_form
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.v3.permissions import require_any_permission
from wagtail.api.v3.registry import registry
from wagtail.api.v3.schemas.base import build_union_schemas
from wagtail.coreutils import resolve_model_string
from wagtail.snippets.api.schemas import ParamTypeInjectingBody
from wagtail.snippets.models import get_snippet_models

router = Router(tags=["snippets"])

enabled_models = [
    model for model in get_snippet_models() if registry.has(model._meta.label)
]


if enabled_models:
    _snippet_type_labels = tuple(model._meta.label for model in enabled_models)
    SnippetTypeLiteral = Literal[_snippet_type_labels]  # ty: ignore[invalid-type-form]
    _snippet_schemas = build_union_schemas(enabled_models)
    SnippetDetailSchema = _snippet_schemas.detail
    SnippetCreateSchema = _snippet_schemas.create
    SnippetUpdateSchema = _snippet_schemas.update
else:
    # No snippet models are registered - fall back to a type/schema that can
    # never match a real request, so the router still imports (and the
    # OpenAPI schema still generates) with no snippet models to build a
    # union from.
    SnippetTypeLiteral = Literal[""]

    class _NoSnippetModelsSchema(Schema):
        meta: Any = None

    SnippetDetailSchema = SnippetCreateSchema = SnippetUpdateSchema = (
        _NoSnippetModelsSchema
    )


def get_model_from_params(request, *args, type: SnippetTypeLiteral, **kwargs):
    return resolve_model_string(type)


@router.get(
    "/{type}/",
    response=list[SnippetDetailSchema],
    url_name="list_snippets",
    summary="List snippets",
    operation_id="snippets_list",
)
@paginate(WagtailLimitOffsetPagination)
@require_any_permission(get_model_from_params, ("add", "change", "delete", "view"))
def list_snippets(request: HttpRequest, type: SnippetTypeLiteral):
    model = resolve_model_string(type)
    return model._default_manager.order_by("pk")


@router.get(
    "/{type}/{pk}/",
    response=SnippetDetailSchema,
    url_name="detail_snippet",
    summary="Snippet detail",
    operation_id="snippets_detail",
)
@require_any_permission(get_model_from_params, ("add", "change", "delete", "view"))
def get_snippet(request: HttpRequest, type: SnippetTypeLiteral, pk: str):
    model = resolve_model_string(type)
    return get_object_or_404(model, pk=pk)


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
):
    model = resolve_model_string(type)
    form = build_model_form(model, data)
    action = CreateAction(
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
):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=pk)
    form = build_model_update_form(instance, data)
    action = EditAction(
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
@require_any_permission(get_model_from_params, ("delete",))
def delete_snippet(request: HttpRequest, type: SnippetTypeLiteral, pk: str):
    model = resolve_model_string(type)
    instance = get_object_or_404(model, pk=pk)
    action = DeleteAction(instance, user=request.user)
    action.execute()
    return Status(204, None)
