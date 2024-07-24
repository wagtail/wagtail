"""Utilities for tests in the `laces` package."""

from django.forms import widgets


class MediaAssertionMixin:
    @staticmethod
    def assertMediaEqual(first: widgets.Media, second: widgets.Media) -> bool:
        """
        Compare two `Media` instances.

        The `Media` class does not implement `__eq__`, but its `__repr__` shows how to
        recreate the instance.
        We can use this to compare two `Media` instances.

        Parameters
        ----------
        first : widgets.Media
            First `Media` instance.
        second : widgets.Media
            Second `Media` instance.

        Returns
        -------
        bool
            Whether the two `Media` instances are equal.

        """
        return repr(first) == repr(second)
