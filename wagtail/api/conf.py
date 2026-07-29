from django.core.exceptions import FieldDoesNotExist
from django.db.models import Model


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
                    model._meta.get_field(field.name)
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
