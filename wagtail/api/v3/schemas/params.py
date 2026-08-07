from typing import ClassVar, Literal, Optional

from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.params.models import Body, BodyModel
from ninja.types import DictStrAny
from pydantic import TypeAdapter
from typing_extensions import NotRequired, TypedDict


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
