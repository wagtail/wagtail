from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from wagtail.wagtailcore.models import Page


class Command(BaseCommand):

    help = 'Resets url_path fields on each page recursively'

    def set_subtree(self, root, root_path):
        root.url_path = root_path
        root.save(update_fields=['url_path'])
        for child in root.get_children():
            self.set_subtree(child, root_path + child.slug + '/')

    def handle(self, *args, **options):
        for node in Page.get_root_nodes():
            self.set_subtree(node, '/')
