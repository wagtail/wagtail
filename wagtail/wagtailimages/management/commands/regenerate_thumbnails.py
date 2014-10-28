from __future__ import print_function
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.wagtailimages.models import Rendition


class Command(BaseCommand):
    def handle(self, **options):
        print('Checking thumbnails')
        for ren in Rendition.objects.all():
            if not os.path.exists(ren.file.path):
                print('Regenerating: ' + ren.file.path)
                thumb = ren.filter.process_image(ren.image.file)
                with open(ren.file.path, 'w') as output:
                    output.write(thumb.read())

