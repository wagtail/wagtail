from http import HTTPStatus
from typing import Any

from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, HttpResponse
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError
from ninja.errors import ValidationError as NinjaValidationError
from pydantic import ValidationError as PydanticValidationError
from pydantic_core import PydanticCustomError

from wagtail.api.rich_text import RichTextFormatError
from wagtail.coreutils import camelcase_to_underscore
from wagtail.utils.forms import FormValidationError

PROBLEM_JSON = "application/problem+json"
DEFAULT_PROBLEM_TYPE = "about:blank"


def _status_title(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


def as_validation_error(
    exc: Exception,
    message: str | None = None,
    loc=(),
) -> PydanticValidationError:
    """
    Adapt a domain error into a Pydantic validation error (HTTP 422).

    Useful for converting exceptions raised in code that is normally caught
    via other mechanisms e.g. Django form validation or prevented by normal
    user interface.

    The ``loc`` argument is best-effort, as the caller may not have enough
    context to provide a full path to the field that caused the error. It may
    also be different to how Ninja normally reports validation errors, which is
    based on the request shape (i.e. may include "body" or "query").
    """
    return PydanticValidationError.from_exception_data(
        "Validation error",
        [
            {
                "type": PydanticCustomError(
                    camelcase_to_underscore(exc.__class__.__name__),
                    message or str(exc),  # type: ignore (LiteralString requirement)
                ),
                "loc": loc,
                "input": None,
            }
        ],
        hide_input=True,
    )


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
        # Use str fallback when errors contain non-serializable objects
        payload.model_dump_json(exclude_none=True, fallback=str),
        status=status,
        content_type=PROBLEM_JSON,
    )


def register_exception_handlers(api: NinjaAPI):
    """Map API exceptions to RFC 7807 ``application/problem+json`` responses.

    Validation errors use status 422 (Unprocessable Entity), which is the usual
    RFC 7807 choice for request validation failures.
    """

    @api.exception_handler(PydanticValidationError)
    @api.exception_handler(NinjaValidationError)
    @api.exception_handler(DjangoValidationError)
    def validation_error_handler(
        request: HttpRequest,
        exc: FormValidationError
        | DjangoValidationError
        | NinjaValidationError
        | PydanticValidationError,
    ):
        if isinstance(exc, FormValidationError):
            errors = [
                {"type": code, "loc": list(path), "msg": message}
                for path, coded_messages in exc.loc_errors
                for message, code in coded_messages
            ]
        elif isinstance(exc, DjangoValidationError):
            errors = [{"msg": msg} for msg in exc.messages]
        elif isinstance(exc, NinjaValidationError):
            errors = exc.errors
        else:  # PydanticValidationError
            # Ninja's validation error replaces Pydantic's input hints with a
            # more user-friendly version, and is already handled above. We use
            # Pydantic directly for internal validation logic, and its "input"
            # hints may be irrelevant to API consumers, so remove them.
            errors = [
                {key: value for key, value in error.items() if key != "input"}
                for error in exc.errors()
            ]
        return problem_response(
            status=422,
            detail="Validation failed",
            errors=errors,
        )

    @api.exception_handler(PermissionDenied)
    def permission_denied_handler(request: HttpRequest, exc: PermissionDenied):
        # v3 never trusts session auth: 401 unless a bearer token resolved.
        if not request.user.is_authenticated:
            return problem_response(status=401, detail="Authentication required")
        return problem_response(status=403, detail=str(exc) or "Permission denied")

    @api.exception_handler(Http404)
    def not_found_handler(request: HttpRequest, exc: Http404):
        return problem_response(status=404, detail=str(exc) or "Not found")

    @api.exception_handler(HttpError)
    def http_error_handler(request: HttpRequest, exc: HttpError):
        return problem_response(status=exc.status_code, detail=str(exc))

    @api.exception_handler(RichTextFormatError)
    def rich_text_format_error_handler(request: HttpRequest, exc: RichTextFormatError):
        return problem_response(status=400, detail=str(exc))

    @api.exception_handler(Exception)
    def unhandled_exception_handler(request: HttpRequest, exc: Exception):
        from django.conf import settings

        if not settings.DEBUG:
            raise exc
        return problem_response(status=500, detail=str(exc))
