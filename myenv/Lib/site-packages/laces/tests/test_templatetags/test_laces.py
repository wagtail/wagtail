import os
import random

from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from django.conf import settings
from django.template import Context, Template, TemplateSyntaxError
from django.test import SimpleTestCase
from django.utils.html import format_html

from laces.components import Component


if TYPE_CHECKING:
    from typing import Any, Dict, List

    from django.utils.safestring import SafeString

    from laces.typing import RenderContext


class CopyingMock(MagicMock):
    """
    A mock that stores copies of the call arguments.

    The default behaviour of a mock is to store references to the call arguments. This
    means that if the call arguments are mutable, then the stored call arguments will
    change when the call arguments are changed. This is not always desirable. E.g. the
    `django.template.Context` class is mutable and the different layers are popped off
    the context during rendering. This makes it hard to inspect the context that was
    passed to a mock.

    This variant of the mock stores copies of the call arguments. This means that the
    stored call arguments will not change when the actual call arguments are changed.

    This override is based on the Python docs:
    https://docs.python.org/3/library/unittest.mock-examples.html#coping-with-mutable-arguments  # noqa: E501
    """

    def __call__(self, /, *args: "List[Any]", **kwargs: "Dict[str, Any]") -> "Any":
        args = deepcopy(args)
        kwargs = deepcopy(kwargs)
        return super().__call__(*args, **kwargs)


class TestComponentTag(SimpleTestCase):
    """
    Test for the `component` template tag.

    Extracted from Wagtail. See:
    https://github.com/wagtail/wagtail/blob/main/wagtail/admin/tests/test_templatetags.py#L225-L305  # noqa: E501
    """

    def setUp(self) -> None:
        self.parent_template = Template("")

        class ExampleComponent(Component):
            # Using a mock to be able to check if the `render_html` method is called.
            render_html = CopyingMock(return_value="Rendered HTML")

        self.component = ExampleComponent()

    def set_parent_template(self, template_string: str) -> None:
        template_string = "{% load laces %}" + template_string
        self.parent_template = Template(template_string)

    def render_parent_template_with_context(
        self,
        context: "RenderContext",
    ) -> "SafeString":
        """
        Render the parent template with the given context.

        Parameters
        ----------
        context: RenderContext
            Context to render the parent template with.

        Returns
        -------
        SafeString
            The parent template rendered with the given context.
        """
        return self.parent_template.render(Context(context))

    def assertVariablesAvailableInRenderHTMLParentContext(
        self,
        expected_context_variables: "Dict[str, Any]",
    ) -> None:
        """
        Assert that the variables defined in the given dictionary are available in the
        parent context of the `render_html` method.

        Keys and values are checked.
        """
        actual_context = self.component.render_html.call_args.args[0]

        for key, value in expected_context_variables.items():
            self.assertIn(key, actual_context)
            actual_value = actual_context[key]
            if not isinstance(actual_value, Component):
                # Because we are inspecting copies of the context variables, we cannot
                # easily compare the components by identity. For now, we just
                # skip components.
                self.assertEqual(actual_value, value)

    def test_render_html_return_in_parent_template(self) -> None:
        self.assertEqual(self.component.render_html(), "Rendered HTML")
        self.set_parent_template("Before {% component my_component %} After")

        result = self.render_parent_template_with_context(
            {"my_component": self.component},
        )

        # This matches the return value of the `render_html` method inserted into the
        # parent template.
        self.assertEqual(result, "Before Rendered HTML After")

    def test_render_html_return_is_escaped(self) -> None:
        self.component.render_html.return_value = (
            "Look, I'm running with scissors! 8< 8< 8<"
        )
        self.set_parent_template("{% component my_component %}")

        result = self.render_parent_template_with_context(
            {"my_component": self.component},
        )

        self.assertEqual(
            result,
            "Look, I&#x27;m running with scissors! 8&lt; 8&lt; 8&lt;",
        )

    def test_render_html_return_not_escaped_when_formatted_html(self) -> None:
        self.component.render_html.return_value = format_html("<h1>My component</h1>")
        self.set_parent_template("{% component my_component %}")

        result = self.render_parent_template_with_context(
            {"my_component": self.component},
        )

        self.assertEqual(result, "<h1>My component</h1>")

    def test_render_html_return_not_escaped_when_actually_rendered_template(
        self,
    ) -> None:
        example_template_name = f"example-{random.randint(1000, 10000)}.html"
        example_template = (
            Path(settings.PROJECT_DIR) / "templates" / example_template_name
        )
        with open(example_template, "w") as f:
            f.write("<h1>My component</h1>")

        # -----------------------------------------------------------------------------
        class RealExampleComponent(Component):
            template_name = example_template_name

        # -----------------------------------------------------------------------------
        component = RealExampleComponent()
        self.set_parent_template("{% component my_component %}")

        result = self.render_parent_template_with_context(
            {"my_component": component},
        )

        self.assertEqual(result, "<h1>My component</h1>")
        os.remove(example_template)

    def test_render_html_parent_context_when_only_component_in_context(self) -> None:
        self.set_parent_template("{% component my_component %}")

        self.render_parent_template_with_context({"my_component": self.component})

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {"my_component": self.component}
        )

    def test_render_html_parent_context_when_other_variable_in_context(self) -> None:
        self.set_parent_template("{% component my_component %}")

        self.render_parent_template_with_context(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

    def test_render_html_parent_context_when_with_block_sets_extra_context(
        self,
    ) -> None:
        self.set_parent_template(
            "{% with test='something' %}{% component my_component %}{% endwith %}"
        )

        self.render_parent_template_with_context({"my_component": self.component})

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

    def test_render_html_parent_context_when_with_keyword_sets_extra_context(
        self,
    ) -> None:
        self.set_parent_template("{% component my_component with test='something' %}")

        self.render_parent_template_with_context({"my_component": self.component})

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

    def test_render_html_parent_context_when_with_only_keyword_limits_extra_context(
        self,
    ) -> None:
        self.set_parent_template(
            "{% component my_component with test='nothing else' only %}"
        )

        self.render_parent_template_with_context(
            {
                "my_component": self.component,
                "other": "something else",
            }
        )

        # The `my_component` and `other` variables from the parent's rendering context
        # are not included in the context that is passed to the `render_html` method.
        # The `test` variable, that was defined with the with-keyword, is present
        # though. Both of these effects come form the `only` keyword.
        self.assertVariablesAvailableInRenderHTMLParentContext({"test": "nothing else"})

    def test_render_html_parent_context_when_with_block_overrides_context(self) -> None:
        self.set_parent_template(
            "{% with test='something else' %}{% component my_component %}{% endwith %}"
        )

        self.render_parent_template_with_context(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                # The `test` variable is overriden by the `with` block.
                "test": "something else",
            }
        )

    def test_render_html_parent_context_when_with_keyword_overrides_context(
        self,
    ) -> None:
        self.set_parent_template(
            "{% component my_component with test='something else' %}"
        )

        self.render_parent_template_with_context(
            {
                "my_component": self.component,
                "test": "something",
            }
        )

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                # The `test` variable is overriden by the `with` keyword.
                "test": "something else",
            },
        )

    def test_render_html_parent_context_when_with_keyword_overrides_with_block(
        self,
    ) -> None:
        self.set_parent_template(
            """
            {% with test='something' %}
            {% component my_component with test='something else' %}
            {% endwith %}
            """
        )

        self.render_parent_template_with_context({"my_component": self.component})

        self.assertVariablesAvailableInRenderHTMLParentContext(
            {
                "my_component": self.component,
                "test": "something else",
            }
        )

    def test_fallback_render_method_arg_true_and_object_with_render_method(
        self,
    ) -> None:
        # -----------------------------------------------------------------------------
        class ExampleNonComponentWithRenderMethod:
            def render(self) -> str:
                return "Rendered non-component"

        # -----------------------------------------------------------------------------
        non_component = ExampleNonComponentWithRenderMethod()
        self.set_parent_template(
            "{% component my_non_component fallback_render_method=True %}"
        )

        result = self.render_parent_template_with_context(
            {"my_non_component": non_component},
        )

        self.assertEqual(result, "Rendered non-component")

    def test_fallback_render_method_arg_true_but_object_without_render_method(
        self,
    ) -> None:
        # -----------------------------------------------------------------------------
        class ExampleNonComponentWithoutRenderMethod:
            pass

        # -----------------------------------------------------------------------------
        non_component = ExampleNonComponentWithoutRenderMethod()
        self.set_parent_template(
            "{% component my_non_component fallback_render_method=True %}"
        )

        with self.assertRaises(ValueError):
            self.render_parent_template_with_context(
                {"my_non_component": non_component},
            )

    def test_no_fallback_render_method_arg_and_object_without_render_method(
        self,
    ) -> None:
        # -----------------------------------------------------------------------------
        class ExampleNonComponentWithoutRenderMethod:
            def __repr__(self) -> str:
                return "<Example repr>"

        # -----------------------------------------------------------------------------
        non_component = ExampleNonComponentWithoutRenderMethod()
        self.set_parent_template("{% component my_non_component %}")

        with self.assertRaises(ValueError) as cm:
            self.render_parent_template_with_context(
                {"my_non_component": non_component},
            )
        self.assertEqual(
            str(cm.exception),
            "Cannot render <Example repr> as a component",
        )

    def test_as_keyword_stores_render_html_return_as_variable(self) -> None:
        self.set_parent_template(
            "{% component my_component as my_var %}The result was: {{ my_var }}"
        )

        result = self.render_parent_template_with_context(
            {"my_component": self.component},
        )

        self.assertEqual(result, "The result was: Rendered HTML")

    def test_as_keyword_without_variable_name(self) -> None:
        # The template is already parsed when the parent template is set. This is the
        # moment where the parsing error is raised.
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.set_parent_template("{% component my_component as %}")

        self.assertEqual(
            str(cm.exception),
            "'component' tag with 'as' must be followed by a variable name",
        )

    def test_autoescape_off_block_can_disable_escaping_of_render_html_return(
        self,
    ) -> None:
        self.component.render_html.return_value = (
            "Look, I'm running with scissors! 8< 8< 8<"
        )
        self.set_parent_template(
            "{% autoescape off %}{% component my_component %}{% endautoescape %}"
        )

        result = self.render_parent_template_with_context(
            {"my_component": self.component},
        )

        self.assertEqual(
            result,
            "Look, I'm running with scissors! 8< 8< 8<",
        )

    def test_parsing_no_arguments(self) -> None:
        # The template is already parsed when the parent template is set. This is the
        # moment where the parsing error is raised.
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.set_parent_template("{% component %}")

        self.assertEqual(
            str(cm.exception),
            "'component' tag requires at least one argument, the component object",
        )

    def test_parsing_unknown_kwarg(self) -> None:
        # The template is already parsed when the parent template is set. This is the
        # moment where the parsing error is raised.
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.set_parent_template("{% component my_component unknown_kwarg=True %}")

        self.assertEqual(
            str(cm.exception),
            "'component' tag only accepts 'fallback_render_method' as a keyword argument",
        )

    def test_parsing_unknown_bit(self) -> None:
        # The template is already parsed when the parent template is set. This is the
        # moment where the parsing error is raised.
        with self.assertRaises(TemplateSyntaxError) as cm:
            self.set_parent_template("{% component my_component unknown_bit %}")

        self.assertEqual(
            str(cm.exception),
            "'component' tag received an unknown argument: 'unknown_bit'",
        )
