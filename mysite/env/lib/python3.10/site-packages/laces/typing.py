from typing import TYPE_CHECKING, Protocol, Union


if TYPE_CHECKING:
    from typing import Any, Optional, TypeAlias

    from django.forms.widgets import Media
    from django.template import Context
    from django.utils.safestring import SafeString

    RenderContext: TypeAlias = Union[Context, dict[str, Any]]


class HasRenderHtmlMethod(Protocol):
    def render_html(  # noqa: E704
        self,
        parent_context: "Optional[RenderContext]",
    ) -> "SafeString": ...


class HasRenderMethod(Protocol):
    def render(  # noqa: E704
        self,
    ) -> "SafeString": ...


Renderable: "TypeAlias" = Union[HasRenderHtmlMethod, HasRenderMethod]


class HasMediaProperty(Protocol):
    @property
    def media(self) -> "Media": ...  # noqa: E704
