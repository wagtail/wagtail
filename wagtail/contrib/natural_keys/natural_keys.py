"""
Natural key implementations for Wagtail models to enable Django serialization framework.
This part adds natural_key() and get_by_natural_key() methods to Wagtail models to enable proper serialization/deserialization.
"""

from django.contrib.contenttypes.models import ContentType
from django.db import models
from wagtail.models import Page, Site
from wagtail.models.media import Collection


def add_natural_key_to_page():
    
    def natural_key(self):
        
        return (self.url_path,)
    
    def get_by_natural_key(cls, url_path):
        
        return cls.objects.get(url_path=url_path)
    
    Page.natural_key = natural_key
    Page.get_by_natural_key = classmethod(get_by_natural_key)


def add_natural_key_to_collection():
    
    def natural_key(self):
        
        path = []
        current = self
        while current.get_parent() is not None:  # Not root
            path.insert(0, current.name)
            current = current.get_parent()
        return tuple(path)
    
    def get_by_natural_key(cls, *path_names):
        """Get collection by hierarchical path."""
        if not path_names:
            raise ValueError("At least one path name must be provided")
            
        # Start from root
        current = cls.get_first_root_node()
        
        # Navigate through the path
        for name in path_names[1:]:  
            try:
                current = current.get_children().get(name=name)
            except cls.DoesNotExist:
                raise cls.DoesNotExist(
                    f"Collection path not found: {'/'.join(path_names)}"
                )
        
        return current
    
    # Add methods to Collection class
    Collection.natural_key = natural_key
    Collection.get_by_natural_key = classmethod(get_by_natural_key)


def add_natural_key_to_image():
    """Add natural key methods to Image model."""
    try:
        from wagtail.images.models import Image
        
        def natural_key(self):
            """Return collection path and filename as natural key."""
            collection_path = self.collection.natural_key()
            return collection_path + (self.file.name,)
        
        def get_by_natural_key(cls, *path_and_filename):
            """Get image by collection path and filename."""
            if len(path_and_filename) < 2:
                raise ValueError("Path and filename must be provided")
            
            filename = path_and_filename[-1]
            collection_path = path_and_filename[:-1]
            
            collection = Collection.objects.get_by_natural_key(*collection_path)
            return cls.objects.get(collection=collection, file=filename)
        
        # Add methods to Image class
        Image.natural_key = natural_key
        Image.get_by_natural_key = classmethod(get_by_natural_key)
        
    except ImportError:
        # wagtail.images if not available
        pass


def add_natural_key_to_document():
    
    try:
        from wagtail.documents.models import Document
        
        def natural_key(self):
            
            collection_path = self.collection.natural_key()
            return collection_path + (self.file.name,)
        
        def get_by_natural_key(cls, *path_and_filename):
            
            if len(path_and_filename) < 2:
                raise ValueError("Path and filename must be provided")
            
            filename = path_and_filename[-1]
            collection_path = path_and_filename[:-1]
            
            collection = Collection.objects.get_by_natural_key(*collection_path)
            return cls.objects.get(collection=collection, file=filename)
        
        # Add methods to Document class
        Document.natural_key = natural_key
        Document.get_by_natural_key = classmethod(get_by_natural_key)
        
    except ImportError:
        # wagtail.documents if not available
        pass


def setup_wagtail_natural_keys():
    
    add_natural_key_to_page()
    add_natural_key_to_collection()
    add_natural_key_to_image()
    add_natural_key_to_document()


