"""
command to export Wagtail data using natural keys.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from wagtail.models import Page, Site, Collection
from wagtail.images.models import Image
from wagtail.documents.models import Document


class Command(BaseCommand):
    help = 'Export Wagtail data using natural keys for serialization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            default='json',
            choices=['json', 'xml', 'yaml'],
            help='Serialization format (default: json)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (default: stdout)'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            choices=['pages', 'sites', 'collections', 'images', 'documents', 'all'],
            default=['all'],
            help='Models to export (default: all)'
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation (default: 2)'
        )

    def handle(self, *args, **options):
        format_type = options['format']
        output_file = options.get('output')
        models_to_export = options['models']
        indent = options['indent']

        #Collect objects to serialize
        objects_to_serialize = []

        if 'all' in models_to_export or 'sites' in models_to_export:
            self.stdout.write('Exporting sites...')
            objects_to_serialize.extend(Site.objects.all())

        if 'all' in models_to_export or 'collections' in models_to_export:
            self.stdout.write('Exporting collections...')
            objects_to_serialize.extend(Collection.objects.all())

        if 'all' in models_to_export or 'pages' in models_to_export:
            self.stdout.write('Exporting pages...')
            objects_to_serialize.extend(Page.objects.all())

        if 'all' in models_to_export or 'images' in models_to_export:
            try:
                self.stdout.write('Exporting images...')
                objects_to_serialize.extend(Image.objects.all())
            except ImportError:
                self.stdout.write('Images not available, skipping...')

        if 'all' in models_to_export or 'documents' in models_to_export:
            try:
                self.stdout.write('Exporting documents...')
                objects_to_serialize.extend(Document.objects.all())
            except ImportError:
                self.stdout.write('Documents not available, skipping...')

        if not objects_to_serialize:
            self.stdout.write(self.style.WARNING('No objects to export'))
            return

        #Serialize the data
        self.stdout.write(f'Serializing {len(objects_to_serialize)} objects...')
        
        serialized_data = serializers.serialize(
            format_type,
            objects_to_serialize,
            use_natural_foreign_keys=True,
            use_natural_primary_keys=True,
            indent=indent if format_type == 'json' else None
        )

        #Output the data
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(serialized_data)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully exported data to {output_file}')
            )
        else:
            self.stdout.write(serialized_data)
