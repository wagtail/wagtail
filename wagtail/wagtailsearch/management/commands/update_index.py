from django.core.management.base import BaseCommand
from django.db import models

from wagtail.wagtailsearch import Indexed, get_search_backend


class Command(BaseCommand):
    def handle(self, **options):
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
            for obj in model.objects.all():
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

        # Search backend
        if 'backend' in options:
            s = options['backend']
        else:
            s = get_search_backend()

        # Reset the index
        self.stdout.write("Reseting index")
        s.reset_index()

        # Add types
        self.stdout.write("Adding types")
        for model in indexed_models:
            s.add_type(model)

        # Add objects to index
        self.stdout.write("Adding objects")
        results = s.add_bulk(object_set.values())
        if results:
            for result in results:
                self.stdout.write(result[0] + ' ' + str(result[1]))

        # Refresh index
        self.stdout.write("Refreshing index")
        s.refresh_index()
