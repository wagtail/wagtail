from __future__ import absolute_import, unicode_literals


class RemovedInWagtail21Warning(DeprecationWarning):
    pass


removed_in_next_version_warning = RemovedInWagtail21Warning


class RemovedInWagtail22Warning(PendingDeprecationWarning):
    pass
