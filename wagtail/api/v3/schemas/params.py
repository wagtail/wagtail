from typing import Optional

from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.params.models import Body, BodyModel
from ninja.types import DictStrAny


class TypeInjectingBodyModel(BodyModel):
    @classmethod
    def get_request_data(
        cls,
        request: HttpRequest,
        api: NinjaAPI,
        path_params: DictStrAny,
    ) -> Optional[DictStrAny]:
        request_data = super().get_request_data(request, api, path_params) or {}
        if (
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
