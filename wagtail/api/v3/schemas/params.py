from datetime import datetime
from typing import Annotated, ClassVar, Literal, Optional

from django.conf import settings
from django.db import models
from django.db.models import Q, QuerySet
from django.http import HttpRequest, QueryDict
from django.shortcuts import get_object_or_404
from ninja import FilterSchema, NinjaAPI, Schema
from ninja.filter_schema import FilterLookup
from ninja.params.models import Body, BodyModel
from ninja.types import DictStrAny
from pydantic import TypeAdapter, model_validator
from taggit.managers import TaggableManager
from typing_extensions import NotRequired, TypedDict

from wagtail.api.v3.errors import as_validation_error
from wagtail.api.v3.pagination import WagtailLimitOffsetPagination
from wagtail.api.validators import APIFieldValidator, OrderingValidator, bool_adapter
from wagtail.models import Locale, TranslatableMixin
from wagtail.search.backends import get_search_backend
from wagtail.search.backends.base import FilterFieldError, OrderByFieldError
from wagtail.search.index import class_is_indexed


def validate_type(data: dict, meta_type: str):
    class MetaSchema(TypedDict):
        type: NotRequired[Literal[meta_type] | None]  # type: ignore

    class BodySchema(TypedDict):
        meta: NotRequired[MetaSchema | None]

    return TypeAdapter(BodySchema).validate_python(data)


class TypeInjectingBodyModel(BodyModel):
    #: If True, a ``meta.type`` the request body itself provided must match
    #: ``get_meta_type()``'s value exactly, or the request is rejected
    #: outright (422) rather than letting the body's type silently pick a
    #: different, but still validly registered, schema to validate/bind the
    #: request against.
    validate: ClassVar[bool] = False

    @classmethod
    def get_request_data(
        cls,
        request: HttpRequest,
        api: NinjaAPI,
        path_params: DictStrAny,
    ) -> Optional[DictStrAny]:
        request_data = super().get_request_data(request, api, path_params) or {}
        if cls.validate:
            meta_type = cls.get_meta_type(request, api, path_params)
            validate_type(request_data.setdefault("data", {}), meta_type)
            request_data["data"]["meta"] = {
                **(request_data["data"].get("meta") or {}),
                "type": meta_type,
            }
        elif (
            isinstance(data := request_data.get("data"), dict)
            and isinstance(meta := (data.setdefault("meta", {}) or {}), dict)
            and not meta.get("type")
            and (meta_type := cls.get_meta_type(request, api, path_params))
        ):
            meta["type"] = meta_type
            data["meta"] = meta
        return request_data

    @classmethod
    def get_meta_type(
        cls,
        request: HttpRequest,
        api: NinjaAPI,
        path_params: DictStrAny,
    ) -> str:
        return NotImplemented


class TypeInjectingBody(Body):
    _model = TypeInjectingBodyModel

    @classmethod
    def _param_source(cls) -> str:
        # Match Body's param source instead of the default cls.__name__.lower()
        return Body._param_source()


class APIFieldFilterSchema(Schema, arbitrary_types_allowed=True):
    """Filter a queryset by arbitrary query params matching writable APIFields.

    Generic across content types: ``base_fields`` names the fields every
    model of this kind always allows (e.g. a page's core fields, or a
    model's own primary key), on top of whatever ``queryset.model``'s own
    ``api_fields`` declare.
    """

    raw_params: QueryDict
    base_fields: list[str]
    ignore_fields: set[str] = set()

    @classmethod
    def with_exclude_schemas(cls, schemas: tuple[type[Schema], ...], **kwargs):
        return cls(
            ignore_fields=set().union(
                *(schema.model_fields.keys() for schema in schemas)
            ),
            **kwargs,
        )

    def get_validated_fields(self, queryset: QuerySet) -> list[str]:
        return APIFieldValidator(
            model=queryset.model,
            fields=set(self.raw_params.keys()) - self.ignore_fields,
            base_fields=self.base_fields,
            db_fields_only=True,
            skip_invalid=True,
        ).fields

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        if not (fields := set(self.get_validated_fields(queryset))):
            return queryset
        for field_name in fields:
            # FieldDoesNotExist already handled by APIFieldValidator.
            field = queryset.model._meta.get_field(field_name)
            value = self.raw_params.get(field_name)

            # Convert value into python
            try:
                if "\x00" in str(value):
                    raise ValueError("null characters are not allowed")
                if isinstance(field, models.ForeignKey):
                    value = field.target_field.get_prep_value(value)
                elif isinstance(field, models.BooleanField):
                    # Use Pydantic as it's more lenient than get_prep_value,
                    # matches more closely to v2 API.
                    value = bool_adapter.validate_python(value)
                elif hasattr(field, "get_prep_value"):
                    value = field.get_prep_value(value)

                if isinstance(field, TaggableManager):
                    # Use repeated query params standard for multiple tags
                    for tag in self.raw_params.getlist(field_name):
                        queryset = queryset.filter(**{field_name + "__name": tag})
                else:
                    queryset = queryset.filter(**{field_name: value})
            except ValueError as e:
                raise as_validation_error(
                    e,
                    message=f"Field filter error, '{value}' is not a valid value "
                    f"for {field_name}. ({e})",
                    loc=(field_name,),
                ) from e
        return queryset


class OrderingSchema(Schema):
    """Order a queryset by one or more of its own APIFields.

    Generic across content types: ``base_fields`` (passed to
    ``order_queryset``) names the fields every model of this kind always
    allows to order by, on top of the queryset's own ``api_fields``.
    """

    # Ninja query params always result in a list if the union type has a list,
    # but we use "random" literal (not ["random"]) for better OpenAPI spec.
    order: Literal["random"] | list[str] = []

    def order_queryset(
        self,
        queryset: QuerySet,
        pagination_info: WagtailLimitOffsetPagination.Input,
        base_fields: list[str] | tuple[str] | tuple[()] = (),
    ) -> QuerySet:
        validated_fields = OrderingValidator(
            model=queryset.model,
            fields=self.order,
            base_fields=list(base_fields),
            db_fields_only=True,
            has_offset=bool(pagination_info.offset),
        )
        if validated_fields.fields:
            return queryset.order_by(*validated_fields.fields)
        return queryset


class SearchSchema(Schema):
    """Full-text search a queryset, generic across content types."""

    search: Optional[str] = None
    search_operator: Optional[Literal["and", "or"]] = None

    @model_validator(mode="after")
    def validate_settings(self):
        if self.search and not getattr(settings, "WAGTAILAPI_SEARCH_ENABLED", True):
            raise AssertionError("search is disabled.")
        return self

    def search_queryset(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> QuerySet:
        if self.search is None:
            return queryset
        if not class_is_indexed(queryset.model):
            error = AssertionError(
                f"{queryset.model._meta.object_name} is not indexed for search."
            )
            raise as_validation_error(error, str(error)) from error
        try:
            return get_search_backend().search(
                self.search,
                queryset,
                operator=self.search_operator,
                order_by_relevance="order" not in request.GET,
            )
        except FilterFieldError as e:
            msg = (
                f"Cannot filter by '{e.field_name}' while searching "
                "(field is not indexed)."
            )
            raise as_validation_error(e, msg, loc=(e.field_name,)) from e
        except OrderByFieldError as e:
            msg = (
                f"Cannot order by '{e.field_name}' while searching "
                "(field is not indexed)."
            )
            raise as_validation_error(e, msg, loc=(e.field_name,)) from e


def locale_filter_q(language_code: str) -> Q:
    # Fetch locale separately so it doesn't have to be indexed when searching
    locale = get_object_or_404(Locale, language_code=language_code)
    return Q(locale=locale)


def translation_of_q(instance: TranslatableMixin, inclusive: bool = False) -> Q:
    q = Q(translation_key=instance.translation_key)
    if not inclusive:
        q &= ~Q(pk=instance.pk)
    return q


class TranslationFilterSchema(Schema):
    locale: Optional[str] = None
    translation_of: Optional[str] = None

    def _check_translatable(self, queryset: QuerySet, loc: str) -> None:
        if not issubclass(queryset.model, TranslatableMixin):
            error = AssertionError(
                f"{queryset.model._meta.object_name} is not translatable."
            )
            raise as_validation_error(error, str(error), loc=(loc,)) from error

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        if self.locale:
            self._check_translatable(queryset, "locale")
            queryset = queryset.filter(locale_filter_q(self.locale))

        if self.translation_of:
            self._check_translatable(queryset, "translation_of")
            try:
                instance = queryset.model._default_manager.get(pk=self.translation_of)
            except queryset.model.DoesNotExist as e:
                message = (
                    f"No {queryset.model._meta.object_name} matches the given "
                    f"translation_of value."
                )
                raise as_validation_error(e, message, loc=("translation_of",)) from e
            queryset = queryset.filter(translation_of_q(instance))

        return queryset


class RevisionFilterSchema(FilterSchema):
    created_at_from: Annotated[Optional[datetime], FilterLookup("created_at__gte")] = (
        None
    )
    created_at_to: Annotated[Optional[datetime], FilterLookup("created_at__lte")] = None
    user_id: Optional[int | str] = None
    approved_go_live_at_from: Annotated[
        Optional[datetime],
        FilterLookup("approved_go_live_at__gte"),
    ] = None
    approved_go_live_at_to: Annotated[
        Optional[datetime],
        FilterLookup("approved_go_live_at__lte"),
    ] = None
    object_str: Annotated[Optional[str], FilterLookup("object_str__icontains")] = None
