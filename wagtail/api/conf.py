from django.db.models import Model


class APIField:
    def __init__(self, name, serializer=None):
        self.name = name
        self.serializer = serializer

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"<APIField {self.name}>"

    @classmethod
    def get_fields_for_model(cls, model: type[Model]) -> list["APIField"]:
        """Return a set of :class:`APIField` instances for the given model."""
        return [
            field if isinstance(field, cls) else cls(field)
            for field in getattr(model, "api_fields", ())
        ]
