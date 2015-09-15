from .base import *


DEBUG = False
DEBUG_TEMPLATE = False

for i in range(0, len(TEMPLATES) - 1):
    TEMPLATES[i]['OPTIONS']['debug'] = DEBUG_TEMPLATE


try:
    from .local import *
except ImportError:
    pass
