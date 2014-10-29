from optparse import make_option

from django.core.management.base import BaseCommand
from django.conf import settings

from wagtail.wagtailsearch.index import Indexed, get_indexed_models
from wagtail.wagtailsearch.backends import get_search_backend


class Command(BaseCommand):
    def get_object_list(self):
        # Return list of (model_name, queryset) tuples
        return [
            (model, model.get_indexed_objects())
            for model in get_indexed_models()
        ]

    def update_backend(self, backend_name, object_list):
        # Print info
        self.stdout.write("Updating backend: " + backend_name)

        # Get backend
        backend = get_search_backend(backend_name)

        # Reset the index
        self.stdout.write(backend_name + ": Reseting index")
        backend.reset_index()

        for model, queryset in object_list:
            self.stdout.write(backend_name + ": Indexing model '%s.%s'" % (
                model._meta.app_label,
                model.__name__,
            ))

            # Add type
            backend.add_type(model)

            # Add objects
            backend.add_bulk(model, queryset)

        # Refresh index
        self.stdout.write(backend_name + ": Refreshing index")
        backend.refresh_index()

    option_list = BaseCommand.option_list + (
        make_option('--backend',
            action='store',
            dest='backend_name',
            default=None,
            help="Specify a backend to update",
        ),
    )

    def handle(self, **options):
        # Get object list
        object_list = self.get_object_list()

        # Get list of backends to index
        if options['backend_name']:
            # index only the passed backend
            backend_names = [options['backend_name']]
        elif hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
            # index all backends listed in settings
            backend_names = settings.WAGTAILSEARCH_BACKENDS.keys()
        else:
            # index the 'default' backend only
            backend_names = ['default']

        # Update backends
        for backend_name in backend_names:
            self.update_backend(backend_name, object_list)
