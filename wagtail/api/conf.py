from django.db.models import Model


class APIField:
    def __init__(self, name: str, serializer=None, writable=False):
        self.name = name
        self.serializer = serializer
        self.writable = writable

    def __hash__(self):
        return hash((self.name, self.writable))

    def __repr__(self):
        return f"<APIField {self.name} writable={self.writable}>"

    @classmethod
    def get_fields_for_model(cls, model: type[Model]) -> list["APIField"]:
        """Return a set of :class:`APIField` instances for the given model."""
        return [
            field if isinstance(field, cls) else cls(field)
            for field in getattr(model, "api_fields", ())
        ]

    @classmethod
    def get_writable_fields_for_model(cls, model: type[Model]) -> list["APIField"]:
        """Return a set of writable :class:`APIField` instances for the given model."""
        return [
            field
            for field in getattr(model, "api_fields", ())
            if isinstance(field, cls) and field.writable
        ]
