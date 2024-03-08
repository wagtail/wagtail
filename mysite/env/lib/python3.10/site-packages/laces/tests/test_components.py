import os
import random

from pathlib import Path
from typing import TYPE_CHECKING

from django.conf import settings
from django.forms import widgets
from django.template import Context
from django.test import SimpleTestCase
from django.utils.safestring import SafeString

from laces.components import Component, MediaContainer
from laces.tests.utils import MediaAssertionMixin


if TYPE_CHECKING:
    from typing import Any, Optional, Union

    from laces.typing import RenderContext


class TestComponent(MediaAssertionMixin, SimpleTestCase):
    """Directly test the Component class."""

    def setUp(self) -> None:
        self.component = Component()

    def test_render_html(self) -> None:
        """Test the `render_html` method."""
        # The default Component does not specify a `template_name` attribute which is
        # required for `render_html`. So calling the method on the Component class
        # will raise an error.
        with self.assertRaises(AttributeError):
            self.component.render_html()

    def test_get_context_data_parent_context_empty_context(self) -> None:
        """
        Test the default get_context_data.

        The parent context should not matter, but we use it as it is used in
        `render_html` (which passes a `Context` object).
        """
        result = self.component.get_context_data(parent_context=Context())

        self.assertIsInstance(result, dict)
        self.assertEqual(result, {})

    def test_media(self) -> None:
        """
        Test the `media` property.

        The `media` property is added through the `metaclass=MediaDefiningClass`
        definition.

        """
        empty_media = widgets.Media()
        self.assertIsInstance(self.component.media, widgets.Media)
        self.assertMediaEqual(self.component.media, empty_media)


class TestComponentSubclasses(MediaAssertionMixin, SimpleTestCase):
    """
    Test the Component class through subclasses.

    Most functionality of the Component class is only unlocked through subclassing and
    definition of certain attributes (like `template_name`) or overriding of the
    existing methods. This test class tests the functionality that is unlocked through
    subclassing.
    """

    @classmethod
    def make_example_template_name(cls) -> str:
        return f"example-{random.randint(1000, 10000)}.html"

    @classmethod
    def get_example_template_name(cls) -> str:
        example_template_name = cls.make_example_template_name()
        while os.path.exists(example_template_name):
            example_template_name = cls.make_example_template_name()
        return example_template_name

    def setUp(self) -> None:
        self.example_template_name = self.get_example_template_name()
        self.example_template = (
            Path(settings.PROJECT_DIR) / "templates" / self.example_template_name
        )
        # Write content to the template file to ensure it exists.
        self.set_example_template_content("")

    def set_example_template_content(self, content: str) -> None:
        with open(self.example_template, "w") as f:
            f.write(content)

    def test_render_html_with_template_name_set(self) -> None:
        """
        Test `render_html` method with a set `template_name` attribute.
        """

        # -----------------------------------------------------------------------------
        class ExampleComponent(Component):
            template_name = self.example_template_name

        # -----------------------------------------------------------------------------

        self.set_example_template_content("Test")

        result = ExampleComponent().render_html()

        self.assertIsInstance(result, str)
        self.assertIsInstance(result, SafeString)
        self.assertEqual(result, "Test")

    def test_render_html_with_template_name_set_and_data_from_get_context_data(
        self,
    ) -> None:
        """
        Test `render_html` method with `get_context_data` providing data for the
        context.
        """

        # -----------------------------------------------------------------------------
        class ExampleComponent(Component):
            template_name = self.example_template_name

            def get_context_data(
                self,
                parent_context: "Optional[RenderContext]",
            ) -> "RenderContext":
                return {"name": "World"}

        # -----------------------------------------------------------------------------

        self.set_example_template_content("Hello {{ name }}")

        result = ExampleComponent().render_html()

        self.assertEqual(result, "Hello World")

    def test_render_html_when_get_context_data_returns_None(self) -> None:
        """
        Test `render_html` method when `get_context_data` returns `None`.

        The `render_html` method raises a `TypeError` when `None` is returned from
        `get_context_method`. This behavior was present when the class was extracted
        from Wagtail. It is not totally clear why this specific check is needed. By
        default, the `get_context_data` method provides and empty dict. If an override
        wanted to `get_context_data` return `None`, it should be expected that no
        context data is available during rendering. The underlying `template.render`
        method does not seem to be ok with `None` as the provided context.
        """

        # -----------------------------------------------------------------------------
        class ExampleComponent(Component):
            def get_context_data(
                self,
                parent_context: "Optional[Union[Context, dict[str, Any]]]",
            ) -> None:
                return None

        # -----------------------------------------------------------------------------

        with self.assertRaises(TypeError):
            ExampleComponent().render_html()

    def test_media_defined_through_nested_class(self) -> None:
        """
        Test the `media` property when defined through a nested class.

        The `media` property is added through the `metaclass=MediaDefiningClass`
        definition. This test ensures that the `media` property is available when
        configured through a nested class.
        """

        # -----------------------------------------------------------------------------
        class ExampleComponent(Component):
            class Media:
                css = {"all": ["example.css"]}
                js = ["example.js"]

        # -----------------------------------------------------------------------------

        result = ExampleComponent().media

        self.assertIsInstance(result, widgets.Media)
        self.assertMediaEqual(
            result,
            widgets.Media(css={"all": ["example.css"]}, js=["example.js"]),
        )

    def tearDown(self) -> None:
        os.remove(path=self.example_template)


class TestMediaContainer(MediaAssertionMixin, SimpleTestCase):
    """
    Test the MediaContainer class.

    The `MediaContainer` functionality depends on the `django.forms.widgets.Media`
    class. The `Media` class provides the logic to combine the media definitions of
    multiple objects through its `__add__` method. The `MediaContainer` relies on this
    functionality to provide a `media` property that combines the media definitions of
    its members.

    See also:
    https://docs.djangoproject.com/en/4.2/topics/forms/media
    """

    def setUp(self) -> None:
        self.media_container = MediaContainer()

    def test_empty(self) -> None:
        result = self.media_container.media

        self.assertIsInstance(result, widgets.Media)
        self.assertMediaEqual(result, widgets.Media())

    def test_single_member(self) -> None:
        # -----------------------------------------------------------------------------
        class ExampleClass:
            media = widgets.Media(css={"all": ["example.css"]})

        # -----------------------------------------------------------------------------
        example = ExampleClass()
        self.media_container.append(example)

        result = self.media_container.media

        self.assertIsInstance(result, widgets.Media)
        self.assertMediaEqual(result, example.media)
        self.assertMediaEqual(result, widgets.Media(css={"all": ["example.css"]}))

    def test_two_members_of_same_class(self) -> None:
        # -----------------------------------------------------------------------------
        class ExampleClass:
            media = widgets.Media(css={"all": ["example.css"]}, js=["example.js"])

        # -----------------------------------------------------------------------------
        example_1 = ExampleClass()
        example_2 = ExampleClass()
        self.media_container.append(example_1)
        self.media_container.append(example_2)

        result = self.media_container.media

        self.assertIsInstance(result, widgets.Media)
        self.assertMediaEqual(
            result,
            widgets.Media(css={"all": ["example.css"]}, js=["example.js"]),
        )

    def test_two_members_of_different_classes(self) -> None:
        # -----------------------------------------------------------------------------
        class ExampleClass:
            media = widgets.Media(css={"all": ["shared.css"]}, js=["example.js"])

        class OtherExampleClass:
            media = widgets.Media(
                css={
                    "all": ["other.css", "shared.css"],
                    "print": ["print.css"],
                },
                js=["other.js"],
            )

        # -----------------------------------------------------------------------------
        example = ExampleClass()
        self.media_container.append(example)
        other = OtherExampleClass()
        self.media_container.append(other)

        result = self.media_container.media

        self.assertIsInstance(result, widgets.Media)
        self.assertMediaEqual(
            result,
            widgets.Media(
                css={
                    "all": ["other.css", "shared.css"],
                    "print": ["print.css"],
                },
                js=["example.js", "other.js"],
            ),
        )
