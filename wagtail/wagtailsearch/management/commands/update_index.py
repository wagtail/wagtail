from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings

from wagtail.wagtailsearch import Indexed, get_search_backend


def get_search_backends():
    if hasattr(settings, 'WAGTAILSEARCH_BACKENDS'):
        for backend in settings.WAGTAILSEARCH_BACKENDS.keys():
            yield backend, get_search_backend(backend)
    else:
        yield 'default', get_search_backend('default')


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

    def update_backend(self, backend, models, object_list, backend_name=''):
        # Print info
        self.stdout.write("Updating backend: " + backend_name)

        # Get backend
        if backend is None:
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

    def handle(self, **options):
        # Get object list
        models, object_list = self.get_object_list()

        # Update backends
        if 'backend' in options:
            self.update_backend(options['backend'], models, object_list)
        else:
            for backend_name, backend in get_search_backends():
                self.update_backend(backend, models, object_list, backend_name=backend_name)
