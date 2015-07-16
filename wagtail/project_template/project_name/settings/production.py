from .base import *


DEBUG = False
TEMPLATE_DEBUG = False


try:
    from .local import *
except ImportError:
    pass
