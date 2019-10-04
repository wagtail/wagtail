from django.core.management.base import BaseCommand
from django.db import models
from modelcluster.models import get_all_child_relations

from wagtail.core.models import PageRevision, get_page_models


def replace_in_model(model, from_text, to_text):
    text_field_names = [field.name for field in model._meta.fields if (
        isinstance(field, models.TextField)
        or isinstance(field, models.CharField)
    )
    ]
    updated_fields = []
    for field in text_field_names:
        field_value = getattr(model, field)
        if field_value and (from_text in field_value):
            updated_fields.append(field)
            setattr(model, field, field_value.replace(from_text, to_text))

    if updated_fields:
        model.save(update_fields=updated_fields)


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('from_text')
        parser.add_argument('to_text')

    def handle(self, *args, **options):
        from_text = options['from_text']
        to_text = options['to_text']

        for revision in PageRevision.objects.filter(content_json__contains=from_text):
            revision.content_json = revision.content_json.replace(from_text, to_text)
            revision.save(update_fields=['content_json'])

        for page_class in get_page_models():
            self.stdout.write("scanning %s" % page_class._meta.verbose_name)

            child_relation_names = [rel.get_accessor_name() for rel in get_all_child_relations(page_class)]

            # Find all pages of this exact type; exclude subclasses, as they will
            # appear in the get_page_models() list in their own right, and this
            # ensures that replacement happens only once
            for page in page_class.objects.exact_type(page_class):
                replace_in_model(page, from_text, to_text)
                for child_rel in child_relation_names:
                    for child in getattr(page, child_rel).all():
                        replace_in_model(child, from_text, to_text)
