from django.core.exceptions import FieldDoesNotExist
from django.db.models import Field, ForeignObjectRel, Model


def get_model_field(model: type[Model], name: str) -> Field | ForeignObjectRel:
    """
    Like ``model._meta.get_field(name)``, but also finds a reverse relation by
    its accessor name.

    ``get_field()`` only finds a reverse relation by its query name, which
    differs from the accessor when the relation sets a ``related_query_name``,
    or has no ``related_name``.
    """
    try:
        return model._meta.get_field(name)
    except FieldDoesNotExist:
        for field in model._meta.get_fields():
            if (
                isinstance(field, ForeignObjectRel)
                and field.get_accessor_name() == name
            ):
                return field
        raise


class APIField:
    def __init__(self, name: str, serializer=None, writable=False):
        self.name = name
        self.serializer = serializer
        self.writable = writable

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"<APIField {self.name} writable={self.writable}>"

    @classmethod
    def get_fields_for_model(
        cls,
        model: type[Model],
        db_fields_only=False,
    ) -> list["APIField"]:
        """
        Return a set of :class:`APIField` instances for the given model.

        :param model: The model class to get API fields for.
        :param db_fields_only: If ``True``, only return fields that are also
            Django model fields.
        """
        api_fields = []
        for api_field in getattr(model, "api_fields", ()):
            field = api_field if isinstance(api_field, cls) else cls(api_field)
            if db_fields_only:
                try:
                    get_model_field(model, field.name)
                except FieldDoesNotExist:
                    continue
            api_fields.append(field)
        return api_fields

    @classmethod
    def get_writable_fields_for_model(cls, model: type[Model]) -> list["APIField"]:
        """Return a set of writable :class:`APIField` instances for the given model."""
        return [
            field
            for field in getattr(model, "api_fields", ())
            if isinstance(field, cls) and field.writable
        ]
