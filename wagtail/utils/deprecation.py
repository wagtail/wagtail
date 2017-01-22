from __future__ import absolute_import, unicode_literals


class RemovedInWagtail110Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail110Warning


class RemovedInWagtail111Warning(PendingDeprecationWarning):
    pass
