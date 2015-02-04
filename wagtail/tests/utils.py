from contextlib import contextmanager
import warnings
import sys

from django.contrib.auth import get_user_model
from django.utils import six


class WagtailTestUtils(object):
    def login(self):
        # Create a user
        user = get_user_model().objects.create_superuser(username='test', email='test@email.com', password='password')

        # Login
        self.client.login(username='test', password='password')

        return user

    def assertRegex(self, *args, **kwargs):
        six.assertRegex(self, *args, **kwargs)

    @staticmethod
    @contextmanager
    def ignore_deprecation_warnings():
        with warnings.catch_warnings(record=True) as warning_list:  # catch all warnings
            yield

        # rethrow all warnings that were not DeprecationWarnings
        for w in warning_list:
            if not issubclass(w.category, DeprecationWarning):
                warnings.showwarning(message=w.message, category=w.category, filename=w.filename, lineno=w.lineno, file=w.file, line=w.line)

    # borrowed from https://github.com/django/django/commit/9f427617e4559012e1c2fd8fce46cbe225d8515d
    @staticmethod
    def reset_warning_registry():
        """
        Clear warning registry for all modules. This is required in some tests
        because of a bug in Python that prevents warnings.simplefilter("always")
        from always making warnings appear: http://bugs.python.org/issue4180

        The bug was fixed in Python 3.4.2.
        """
        key = "__warningregistry__"
        for mod in sys.modules.values():
            if hasattr(mod, key):
                getattr(mod, key).clear()
