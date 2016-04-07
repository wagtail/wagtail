from __future__ import absolute_import, unicode_literals

import warnings


class RemovedInWagtail16Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail16Warning


class RemovedInWagtail17Warning(PendingDeprecationWarning):
    pass


class ThisShouldBeAList(list):
    """
    Some properties - such as Indexed.search_fields - used to be tuples. This
    is incorrect, and they should have been lists.  Changing these to be a list
    now would be backwards incompatible, as people do

    .. code-block:: python

        search_fields = Page.search_fields + (
            SearchField('body')
        )

    Adding a tuple to the end of a list causes an error.

    This class will allow tuples to be added to it, as in the above behaviour,
    but will raise a deprecation warning if someone does this.
    """
    message = 'Using a {type} for {name} is deprecated, use a list instead'

    def __init__(self, items, name, category):
        super(ThisShouldBeAList, self).__init__(items)
        self.name = name
        self.category = category

    def _format_message(self, rhs):
        return self.message.format(name=self.name, type=type(rhs).__name__)

    def __add__(self, rhs):
        cls = type(self)
        if isinstance(rhs, tuple):
            # Seems that a tuple was passed in. Raise a deprecation
            # warning, but then keep going anyway.
            message = self._format_message(rhs)
            warnings.warn(message, category=self.category, stacklevel=2)
            rhs = list(rhs)
        return cls(super(ThisShouldBeAList, self).__add__(list(rhs)),
                   name=self.name, category=self.category)


class SearchFieldsShouldBeAList(ThisShouldBeAList):
    """
    Indexed.search_fields was a tuple, but it should have been a list
    """
    def __init__(self, items, name='search_fields', category=RemovedInWagtail17Warning):
        super(SearchFieldsShouldBeAList, self).__init__(items, name, category)
