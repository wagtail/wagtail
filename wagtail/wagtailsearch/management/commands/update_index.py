from optparse import make_option

from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings

from wagtail.wagtailsearch.indexed import Indexed
from wagtail.wagtailsearch.backends import get_search_backend


class Command(BaseCommand):
    def get_object_list(self):
        # Print info
        self.stdout.write("Getting object list")

        # Get list of indexed models
        indexed_models = [model for model in models.get_models() if issubclass(model, Indexed)]

        # Object set
        object_set = {}

        # Add all objects to object set and detect any duplicates
        # Duplicates are caused when both a model and a derived model are indexed
        # Eg, if BlogPost inherits from Page and both of these models are indexed
        # If we were to add all objects from both models into the index, all the BlogPosts will have two entries
        for model in indexed_models:
            # Get toplevel content type
            toplevel_content_type = model.indexed_get_toplevel_content_type()

            # Loop through objects
            for obj in model.get_indexed_objects():
                # Get key for this object
                key = toplevel_content_type + ':' + str(obj.pk)

                # Check if this key already exists
                if key in object_set:
                    # Conflict, work out who should get this space
                    # The object with the longest content type string gets the space
                    # Eg, "wagtailcore.Page-myapp.BlogPost" kicks out "wagtailcore.Page"
                    if len(obj.indexed_get_content_type()) > len(object_set[key].indexed_get_content_type()):
                        # Take the spot
                        object_set[key] = obj
                else:
                    # Space free, take it
                    object_set[key] = obj

        return indexed_models, object_set.values()

    def update_backend(self, backend_name, models, object_list):
        # Print info
        self.stdout.write("Updating backend: " + backend_name)

        # Get backend
        backend = get_search_backend(backend_name)

        # Reset the index
        self.stdout.write(backend_name + ": Reseting index")
        backend.reset_index()

        # Add types
        self.stdout.write(backend_name + ": Adding types")
        for model in models:
            backend.add_type(model)

        # Add objects to index
        self.stdout.write(backend_name + ": Adding objects")
        for result in backend.add_bulk(object_list):
            self.stdout.write(result[0] + ' ' + str(result[1]))

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
        models, object_list = self.get_object_list()

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
            self.update_backend(backend_name, models, object_list)
