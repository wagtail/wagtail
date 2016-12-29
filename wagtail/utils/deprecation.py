from __future__ import absolute_import, unicode_literals


class RemovedInWagtail19Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail19Warning


class RemovedInWagtail110Warning(PendingDeprecationWarning):
    pass
