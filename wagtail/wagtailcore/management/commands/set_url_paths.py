from __future__ import absolute_import, unicode_literals

from django.core.management.base import BaseCommand

from wagtail.wagtailcore.models import Page


class Command(BaseCommand):

    help = 'Resets url_path fields on each page recursively'

    def set_subtree(root, parent=None):
        root.specific.set_url_path(parent)
        root.save(update_fields=['url_path'])
        for child in root.get_children():
            set_subtree(child.specific, root)

    def handle(self, *args, **options):
        for node in Page.get_root_nodes():
            set_subtree(node)
