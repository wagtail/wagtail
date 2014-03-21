from django.core.exceptions import ImproperlyConfigured

class BaseFormProcessor(object):
    def __init__(self):
        pass
    
    def validate_usage(page):
        return True
        
    def process(self, page, form):
        return NotImplemented