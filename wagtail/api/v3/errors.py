from http import HTTPStatus
from typing import Any

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, HttpResponse
from ninja import Schema
from ninja.errors import HttpError
from ninja.errors import ValidationError as NinjaValidationError

PROBLEM_JSON = "application/problem+json"
DEFAULT_PROBLEM_TYPE = "about:blank"


def _status_title(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


class ProblemDetail(Schema):
    type: str
    title: str
    status: int
    detail: str = ""
    errors: list[dict[str, Any]] | None = None


def build_problem_detail(
    *,
    status: int,
    title: str | None = None,
    detail: str = "",
    errors: list[dict[str, Any]] | None = None,
    type_uri: str = DEFAULT_PROBLEM_TYPE,
) -> ProblemDetail:
    return ProblemDetail(
        type=type_uri,
        title=title or _status_title(status),
        status=status,
        detail=detail,
        errors=errors,
    )


def problem_response(
    *,
    status: int,
    title: str | None = None,
    detail: str = "",
    errors: list[dict[str, Any]] | None = None,
    type_uri: str = DEFAULT_PROBLEM_TYPE,
) -> HttpResponse:
    payload = build_problem_detail(
        status=status,
        title=title,
        detail=detail,
        errors=errors,
        type_uri=type_uri,
    )
    return HttpResponse(
        payload.model_dump_json(exclude_none=True),
        status=status,
        content_type=PROBLEM_JSON,
    )


def register_exception_handlers(api):
    """Map API exceptions to RFC 7807 ``application/problem+json`` responses.

    Validation errors use status 422 (Unprocessable Entity), which is the usual
    RFC 7807 choice for request validation failures.
    """

    @api.exception_handler(NinjaValidationError)
    @api.exception_handler(DjangoValidationError)
    def validation_error_handler(
        request: HttpRequest, exc: DjangoValidationError | NinjaValidationError
    ):
        if isinstance(exc, DjangoValidationError):
            errors = [{"message": msg} for msg in exc.messages]
        else:
            errors = exc.errors
        return problem_response(
            status=422,
            detail="Validation failed",
            errors=errors,
        )

    @api.exception_handler(PermissionDenied)
    def permission_denied_handler(request: HttpRequest, exc: PermissionDenied):
        if not request.user.is_authenticated:
            return problem_response(status=401, detail="Authentication required")
        return problem_response(status=403, detail="Permission denied")

    @api.exception_handler(Http404)
    def not_found_handler(request: HttpRequest, exc: Http404):
        return problem_response(status=404, detail=str(exc) or "Not found")

    @api.exception_handler(HttpError)
    def http_error_handler(request: HttpRequest, exc: HttpError):
        return problem_response(status=exc.status_code, detail=str(exc))

    @api.exception_handler(Exception)
    def unhandled_exception_handler(request: HttpRequest, exc: Exception):
        from django.conf import settings

        if not settings.DEBUG:
            raise exc
        return problem_response(status=500, detail=str(exc))
