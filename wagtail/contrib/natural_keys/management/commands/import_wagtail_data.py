"""
command to import Wagtail data using natural keys.
"""

from django.core.management.base import BaseCommand, CommandError
from django.core import serializers
from django.db import transaction


class Command(BaseCommand):
    help = 'Import Wagtail data using natural keys for deserialization'

    def add_arguments(self, parser):
        parser.add_argument(
            'input_file',
            type=str,
            help='Input file path containing serialized data'
        )
        parser.add_argument(
            '--format',
            default='json',
            choices=['json', 'xml', 'yaml'],
            help='Serialization format (default: json)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--ignore-errors',
            action='store_true',
            help='Continue importing even if some objects fail'
        )

    def handle(self, *args, **options):
        input_file = options['input_file']
        format_type = options['format']
        dry_run = options['dry_run']
        ignore_errors = options['ignore_errors']

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = f.read()
        except FileNotFoundError:
            raise CommandError(f'Input file not found: {input_file}')
        except Exception as e:
            raise CommandError(f'Error reading input file: {e}')

        self.stdout.write(f'Deserializing data from {input_file}...')

        try:
            objects = serializers.deserialize(format_type, data)
        except Exception as e:
            raise CommandError(f'Error deserializing data: {e}')

        imported_count = 0
        error_count = 0

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        with transaction.atomic():
            for obj in objects:
                try:
                    if not dry_run:
                        obj.save()
                    imported_count += 1
                    self.stdout.write(f'  ✓ {obj.object.__class__.__name__}: {obj.object}')
                except Exception as e:
                    error_count += 1
                    error_msg = f'  ✗ Error importing {obj.object.__class__.__name__}: {e}'
                    self.stdout.write(self.style.ERROR(error_msg))
                    
                    if not ignore_errors:
                        raise CommandError(f'Import failed: {e}')

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'DRY RUN: Would import {imported_count} objects')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} objects')
            )
            
        if error_count > 0:
            self.stdout.write(
                self.style.WARNING(f'{error_count} objects failed to import')
            )
