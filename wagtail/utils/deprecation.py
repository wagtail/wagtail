from __future__ import absolute_import, unicode_literals


class RemovedInWagtail17Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail17Warning


class RemovedInWagtail18Warning(PendingDeprecationWarning):
    pass
