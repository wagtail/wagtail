import warnings

from modelcluster.contrib.taggit import *  # NOQA


warnings.warn(
    "The modelcluster.tags module has been moved to "
    "modelcluster.contrib.taggit", DeprecationWarning)
