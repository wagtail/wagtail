from django import template

# from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from wagtail.images.tests.utils import Image, get_test_image_file


class TestImageTagNext(TestCase):
    def setUp(self):
        # Create an image for running tests on
        self.image = Image.objects.create(
            title="Test image", file=get_test_image_file()
        )

    def _render_image_tag(self, image, filter_spec, **extra_context):
        # not using .format as we would then have to double escape all the curly braces.
        temp = template.Template(
            "{% load wagtailimages_next %}{% image image_obj " + filter_spec + " %}"
        )
        context_data = {"image_obj": image}
        context_data.update(extra_context)
        context = template.Context(context_data)
        return temp.render(context)

    def test_image_tag(self):
        result = self._render_image_tag(self.image, "'width-400'")

        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure that we return a single actual img tag.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set.
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def test_image_tag_spec_variable(self):
        result = self._render_image_tag(self.image, "spec", spec="width-400")
        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure that we return a single actual img tag.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set.
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def test_image_tag_with_chained_filters(self):
        result = self._render_image_tag(self.image, "'fill-200x200 height-150'")
        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure that we return a single actual img tag.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set.
        self.assertTrue('width="150"' in result)
        self.assertTrue('height="150"' in result)

    def test_image_tag_with_chained_filters_in_variable(self):
        result = self._render_image_tag(
            self.image, "spec", spec="fill-200x200 height-150"
        )
        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure that we return a single actual img tag.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set.
        self.assertTrue('width="150"' in result)
        self.assertTrue('height="150"' in result)

    def test_image_tag_none(self):
        result = self._render_image_tag(None, "'width-500'")
        self.assertEqual(result, "")

    def _render_image_tag_as(self, image, filter_spec, **extra_context):
        temp = template.Template(
            "{% load wagtailimages_next %}"
            "{% image image_obj " + filter_spec + " as test_img %}"
            "<img {{ test_img.attrs }} />"
        )
        context_data = {"image_obj": image}
        context_data.update(extra_context)
        context = template.Context(context_data)
        return temp.render(context)

    def test_image_tag_attrs(self):
        result = self._render_image_tag_as(self.image, "'width-400'")

        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure the template tags usual "img" return value did not render, as we
        # should be storing into a context variable.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('alt="Test image"' in result)

    def _render_image_tag_with_extra_attributes(
        self, image, extra_attributes, **extra_context
    ):
        attributes = " ".join(
            [
                "{key}={value}".format(key=key, value=value)
                for key, value in extra_attributes.items()
            ]
        )
        temp = template.Template(
            "{% load wagtailimages_next %}"
            "{% image image_obj 'width-400' " + attributes + " %}"
        )
        context_data = {"image_obj": image}
        context_data.update(extra_context)
        context = template.Context(context_data)
        return temp.render(context)

    def test_image_tag_with_extra_attributes(self):
        result = self._render_image_tag_with_extra_attributes(
            self.image,
            {'"class"': "'photo'", "'title'": "title|lower", "'alt'": "'Alternate'"},
            title="My Wonderful Title",
        )

        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure the template tags usual "img" return value did not render, as we
        # should be storing into a context variable.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('class="photo"' in result)
        self.assertTrue('alt="Alternate"' in result)
        self.assertTrue('title="my wonderful title"' in result)

    def test_image_tag_with_extra_attributes_as_vars(self):
        result = self._render_image_tag_with_extra_attributes(
            self.image,
            {"dynamic_attr": '"photo"', "'alt'": "'Alternate'"},
            dynamic_attr="aria-label",
        )
        # Check that all tags were rendered.
        self.assertTrue("{%" not in result and "%}" not in result)
        # Ensure that we return a single actual img tag.
        self.assertEqual(result.count("<img"), 1)
        # Check that all the required HTML attributes are set
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)
        self.assertTrue('aria-label="photo"' in result)
        self.assertTrue('alt="Alternate"' in result)

    def _render_image_tag_with_filters(self, image, **extra_context):
        temp = template.Template(
            "{% load wagtailimages_next %}"
            "{% image image_primary|default:image_alternate 'width-400' %}"
        )
        context_data = {"image_primary": None, "image_alternate": image}
        context_data.update(extra_context)
        context = template.Context(context_data)
        return temp.render(context)

    def test_image_tag_with_filters(self):
        result = self._render_image_tag_with_filters(self.image)
        self.assertTrue('width="400"' in result)
        self.assertTrue('height="300"' in result)

    # Note: I disabeled this, as our code supports versions with and without spaces.
    #       I'm not sure I see the point in not supporting the pipe format as well?
    # def test_filter_specs_must_match_allowed_pattern(self):
    # with self.assertRaises(template.TemplateSyntaxError):
    #     self.render_image_tag(self.image, "fill-200x200|height-150")

    def test_invalid_kwarg(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                "{% load wagtailimages_next %} "
                "{% image image_obj 'fill-800x600' 'alt''test' as test_img %} "
                "<img {{ test_img.attrs }} />"
            )

    def test_context_may_only_contain_one_argument(self):
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                "{% load wagtailimages_next %}"
                "{% image image_obj fill-200x200 "
                "as test_img this_one_should_not_be_there %}"
                "<img {{ test_img.attrs }} />"
            )

    def test_no_image_filter_provided(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template("{% load wagtailimages_next %}{% image image_obj %}")

    def test_no_image_filter_provided_when_using_as(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                "{% load wagtailimages_next %}{% image image_obj as foo %}"
            )

    def test_no_image_filter_provided_but_attributes_provided(self):
        # if image template gets the image but no filters
        with self.assertRaises(template.TemplateSyntaxError):
            template.Template(
                "{% load wagtailimages_next %}"
                '{% image image_obj class="cover-image"%}'
            )

    # TODO:
    # def _render_image_url_tag(self, image, view_name, **extra_context):
    #     temp = template.Template(
    #         '{% load wagtailimages_next %}{% image_url image_obj "width-400" "'
    #         + view_name
    #         + '" %}'
    #     )
    #     context_data = {"image_obj": image}
    #     context_data.update(extra_context)
    #     context = template.Context(context_data)
    #     return temp.render(context)

    # def test_image_url(self):
    #     result = self.render_image_url_tag(self.image, "wagtailimages_serve")
    #     self.assertRegex(
    #         result,
    #         "/images/.*/width-400/{}".format(self.image.file.name.split("/")[-1]),
    #     )

    # def test_image_url_custom_view(self):
    #     result = self.render_image_url_tag(
    #         self.image, "wagtailimages_serve_custom_view"
    #     )

    #     self.assertRegex(
    #         result,
    #         "/testimages/custom_view/.*/width-400/{}".format(
    #             self.image.file.name.split("/")[-1]
    #         ),
    #     )

    # def test_image_url_no_imageserve_view_added(self):
    #     # if image_url tag is used, but the image serve view was not defined.
    #     with self.assertRaises(ImproperlyConfigured):
    #         temp = template.Template(
    #             '{% load wagtailimages_next %}{% image_url image_obj "width-400" "mynonexistingimageserve_view" %}'
    #         )
    #         context = template.Context({"image_obj": self.image})
    #         temp.render(context)
