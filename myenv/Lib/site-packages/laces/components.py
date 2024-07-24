from typing import TYPE_CHECKING, List

from django.forms.widgets import Media, MediaDefiningClass
from django.template import Context
from django.template.loader import get_template

from laces.typing import HasMediaProperty


if TYPE_CHECKING:
    from typing import Optional

    from django.utils.safestring import SafeString

    from laces.typing import RenderContext


class Component(metaclass=MediaDefiningClass):
    """
    A class that knows how to render itself.

    Extracted from Wagtail. See:
    https://github.com/wagtail/wagtail/blob/094834909d5c4b48517fd2703eb1f6d386572ffa/wagtail/admin/ui/components.py#L8-L22  # noqa: E501

    A component uses the `MetaDefiningClass` metaclass to add a `media` property, which
    allows the definitions of CSS and JavaScript assets that are associated with the
    component. This works the same as `Media` class used by Django forms.
    See also: https://docs.djangoproject.com/en/4.2/topics/forms/media/
    """

    template_name: str

    def render_html(
        self,
        parent_context: "Optional[RenderContext]" = None,
    ) -> "SafeString":
        """
        Return string representation of the object.

        Given a context dictionary from the calling template (which may be a
        `django.template.Context` object or a plain `dict` of context variables),
        returns the string representation to be rendered.

        This will be subject to Django's HTML escaping rules, so a return value
        consisting of HTML should typically be returned as a
        `django.utils.safestring.SafeString` instance.
        """
        if parent_context is None:
            parent_context = Context()
        context_data = self.get_context_data(parent_context)
        if context_data is None:
            raise TypeError("Expected a dict from get_context_data, got None")

        template = get_template(self.template_name)
        return template.render(context_data)

    def get_context_data(
        self,
        parent_context: "RenderContext",
    ) -> "Optional[RenderContext]":
        return {}

    # fmt: off
    if TYPE_CHECKING:
        # It's ugly, I know. But it seems to be the best way to make `mypy` happy.
        # The `media` property is dynamically added by the `MediaDefiningClass`
        # metaclass. Because of how dynamic it is, `mypy` is not able to pick it up.
        # This is why we need to add a type hint for it here. The other way would be a
        # stub, but that would require the whole module to be stubbed and that is even
        # more annoying to keep up to date.
        @property
        def media(self) -> Media: ...  # noqa: E704
    # fmt: on


class MediaContainer(List[HasMediaProperty]):
    """
    A list that provides a `media` property that combines the media definitions
    of its members.

    Extracted from Wagtail. See:
    https://github.com/wagtail/wagtail/blob/ca8a87077b82e20397e5a5b80154d923995e6ca9/wagtail/admin/ui/components.py#L25-L36  # noqa: E501

    The `MediaContainer` functionality depends on the `django.forms.widgets.Media`
    class. The `Media` class provides the logic to combine the media definitions of
    multiple objects through its `__add__` method. The `MediaContainer` relies on this
    functionality to provide a `media` property that combines the media definitions of
    its members.

    See also:
    https://docs.djangoproject.com/en/4.2/topics/forms/media
    """

    @property
    def media(self) -> Media:
        """
        Return a `Media` object containing the media definitions of all members.

        This makes use of the `Media.__add__` method, which combines the media
        definitions of two `Media` objects.

        """
        media = Media()
        for item in self:
            media += item.media
        return media
