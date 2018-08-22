import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations


class AlterStreamField(migrations.AlterField):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        super().database_forwards(app_label, schema_editor, from_state, to_state)
        from_model = from_state.apps.get_model(app_label, self.model_name)
        to_model = to_state.apps.get_model(app_label, self.model_name)
        for from_obj in from_model.objects.all():
            from_field = getattr(from_obj, self.name)
            from_data = from_field.stream_data
            to_data = self.transform_values(from_data)
            to_obj = to_model.objects.get(pk=from_obj.pk)
            to_field = getattr(to_obj, self.name)
            to_field.stream_data = to_data
            to_obj.save()
            revisions = from_obj.revisions.all()
            for revision in revisions:
                revision_content = json.loads(revision.content_json)
                from_field_content = json.loads(revision_content[self.name])
                to_field_content = self.transform_values(from_field_content)
                revision_content[self.name] = json.dumps(
                    to_field_content, cls=DjangoJSONEncoder
                )
                revision.content_json = json.dumps(
                    revision_content, cls=DjangoJSONEncoder
                )
                revision.save()

    def transform_values(self, values):
        raise NotImplementedError("Subclass should define this")

    def transform_value(self, value):
        raise NotImplementedError("Subclass should define this")
