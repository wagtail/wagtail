from django.core.exceptions import ValidationError
from django.forms import BaseForm

#: A field's location, e.g. ``("title",)`` or, for an InlinePanel-backed
#: formset's child field, ``("carousel_items", 0, "link_page")``.
FieldPath = tuple[str | int, ...]


class FormValidationError(ValidationError):
    """A ``ValidationError`` for a ``dict[FieldPath, list[str]]`` of errors,
    preserving each message's full :data:`FieldPath` - including into
    InlinePanel-backed formsets, which ``ValidationError`` itself has no
    notion of - as ``loc_errors``, alongside the plain
    ``dict[str, list[str]]`` shape ``ValidationError`` itself understands.
    """

    def __init__(self, errors: dict[FieldPath, list[str]]):
        self.loc_errors = list(errors.items())
        super().__init__(
            {
                ".".join(str(part) for part in path): messages
                for path, messages in errors.items()
            }
        )

    @classmethod
    def from_form(cls, form: BaseForm) -> "FormValidationError":
        """Build from a (possibly ``ClusterForm``) form's own errors, via
        :func:`get_form_errors_as_dict`.
        """
        return cls(cls.get_form_errors_as_dict(form))

    @classmethod
    def get_form_errors_as_dict(
        cls, form: BaseForm, path: FieldPath = ()
    ) -> dict[FieldPath, list[str]]:
        """Collect a (possibly ``ClusterForm``) form's errors into a
        ``dict[FieldPath, list[str]]``.

        Starts from ``form.errors.get_json_data()`` (field name -> list of
        ``{"message", "code"}`` dicts) and flattens each entry to its messages.
        Also walks each formset's non-form errors (e.g. a formset-level
        ``clean()``) and each child form's own field errors, since those aren't
        visited by ``form.errors`` alone - filed under the relation name (and
        child index, for child form errors), as neither maps to one of the
        top-level form's own fields.
        """
        errors: dict[FieldPath, list[str]] = {
            (*path, field_name): [error["message"] for error in field_errors]
            for field_name, field_errors in form.errors.get_json_data().items()
        }

        for rel_name, formset in getattr(form, "formsets", {}).items():
            non_form_errors = [
                error["message"] for error in formset.non_form_errors().get_json_data()
            ]
            if non_form_errors:
                errors[(*path, rel_name)] = non_form_errors

            for i, child_form in enumerate(formset.forms):
                errors.update(
                    cls.get_form_errors_as_dict(child_form, path=(*path, rel_name, i))
                )

        return errors
