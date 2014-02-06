from django.core.management.base import NoArgsCommand

from wagtail.wagtailcore.models import Page


class Command(NoArgsCommand):
    def set_subtree(self, root, root_path):
        root.url_path = root_path
        root.save(update_fields=['url_path'])
        for child in root.get_children():
            self.set_subtree(child, root_path + child.slug + '/')

    def handle_noargs(self, **options):
        for node in Page.get_root_nodes():
            self.set_subtree(node, '/')
