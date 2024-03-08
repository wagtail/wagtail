try:
    # python 3
    from collections.abc import MutableMapping
except ImportError:
    # python 2
    from collections import MutableMapping
