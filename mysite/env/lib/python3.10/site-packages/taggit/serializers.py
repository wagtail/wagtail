"""
Django-taggit serializer support

Originally vendored from https://github.com/glemmaPaul/django-taggit-serializer
"""
import json

# Third party
from django.utils.translation import gettext_lazy
from rest_framework import serializers


class TagList(list):
    """
    This tag list subclass adds pretty printing support to the tag list
    serializer
    """

    def __init__(self, *args, **kwargs):
        pretty_print = kwargs.pop("pretty_print", True)
        super().__init__(*args, **kwargs)
        self.pretty_print = pretty_print

    def __add__(self, rhs):
        return TagList(super().__add__(rhs))

    def __getitem__(self, item):
        result = super().__getitem__(item)
        try:
            return TagList(result)
        except TypeError:
            return result

    def __str__(self):
        if self.pretty_print:
            return json.dumps(self, sort_keys=True, indent=4, separators=(",", ": "))
        else:
            return json.dumps(self)


class TagListSerializerField(serializers.ListField):
    """
    A serializer field that can write out a tag list

    This serializer field has some odd qualities compared to just using a ListField.
    If this field poses problems, we should introduce a new field that is a simpler
    ListField implementation with less features.
    """

    child = serializers.CharField()
    default_error_messages = {
        "not_a_list": gettext_lazy(
            'Expected a list of items but got type "{input_type}".'
        ),
        "invalid_json": gettext_lazy(
            "Invalid json list. A tag list submitted in string"
            " form must be valid json."
        ),
        "not_a_str": gettext_lazy("All list items must be of string type."),
    }
    order_by = None

    def __init__(self, **kwargs):
        pretty_print = kwargs.pop("pretty_print", True)

        style = kwargs.pop("style", {})
        kwargs["style"] = {"base_template": "textarea.html"}
        kwargs["style"].update(style)

        super().__init__(**kwargs)

        self.pretty_print = pretty_print

    def to_internal_value(self, value):
        # note to future maintainers: this field used to not be a ListField
        # and has extra behavior to support string-based input.
        #
        # In the future we should look at removing this feature so we can
        # make this a simple ListField (if feasible)
        if isinstance(value, str):
            if not value:
                value = "[]"
            try:
                value = json.loads(value)
            except ValueError:
                self.fail("invalid_json")

        if not isinstance(value, list):
            self.fail("not_a_list", input_type=type(value).__name__)

        for s in value:
            if not isinstance(s, str):
                self.fail("not_a_str")

            self.child.run_validation(s)

        return value

    def to_representation(self, value):
        if not isinstance(value, TagList):
            if not isinstance(value, list):
                if self.order_by:
                    tags = value.all().order_by(*self.order_by)
                else:
                    tags = value.all()
                value = [tag.name for tag in tags]
            value = TagList(value, pretty_print=self.pretty_print)

        return value


class TaggitSerializer(serializers.Serializer):
    def create(self, validated_data):
        to_be_tagged, validated_data = self._pop_tags(validated_data)

        tag_object = super().create(validated_data)

        return self._save_tags(tag_object, to_be_tagged)

    def update(self, instance, validated_data):
        to_be_tagged, validated_data = self._pop_tags(validated_data)

        tag_object = super().update(instance, validated_data)

        return self._save_tags(tag_object, to_be_tagged)

    def _save_tags(self, tag_object, tags):
        for key in tags.keys():
            tag_values = tags.get(key)
            getattr(tag_object, key).set(tag_values)

        return tag_object

    def _pop_tags(self, validated_data):
        to_be_tagged = {}

        for key in self.fields.keys():
            field = self.fields[key]
            if isinstance(field, TagListSerializerField):
                if key in validated_data:
                    to_be_tagged[key] = validated_data.pop(key)

        return (to_be_tagged, validated_data)
