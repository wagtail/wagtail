from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from wagtail.models import ReferenceIndex


def model_name(model):
    return f"{model.__module__}.{model.__name__}"


class Command(BaseCommand):
    def handle(self, **options):
        self.stdout.write("Reference index entries:")
        object_count = 0

        for model in sorted(apps.get_models(), key=lambda m: model_name(m)):
            if not ReferenceIndex.is_indexed(model):
                continue

            content_types = [
                ContentType.objects.get_for_model(
                    model_or_object, for_concrete_model=False
                )
                for model_or_object in ([model] + model._meta.get_parent_list())
            ]
            content_type = content_types[0]
            base_content_type = content_types[-1]

            count = ReferenceIndex.objects.filter(
                content_type=content_type, base_content_type=base_content_type
            ).count()
            self.stdout.write(f"{count:>6}  {model_name(model)}")
            object_count += count

        self.stdout.write(f"Total entries: {object_count}")
