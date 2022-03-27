# Sendfile "streaming" backend
# This is based on sendfiles builtin "simple" backend but uses a StreamingHttpResponse

import os
import stat
from email.utils import mktime_tz, parsedate_tz
from wsgiref.util import FileWrapper

from django.http import HttpResponseNotModified, StreamingHttpResponse
from django.utils.http import http_date


def sendfile(request, filename, **kwargs):
    # Respect the If-Modified-Since header.
    statobj = os.stat(filename)

    if not was_modified_since(
        request.META.get("HTTP_IF_MODIFIED_SINCE"),
        statobj[stat.ST_MTIME],
    ):
        return HttpResponseNotModified()

    response = StreamingHttpResponse(FileWrapper(open(filename, "rb")))

    response["Last-Modified"] = http_date(statobj[stat.ST_MTIME])
    return response


def was_modified_since(header=None, mtime=0):
    """
    Was something modified since the user last downloaded it?

    header
      This is the value of the If-Modified-Since header.  If this is None,
      I'll just return True.

    mtime
      This is the modification time of the item we're talking about.
    """
    try:
        if header is None:
            raise ValueError
        header_date = parsedate_tz(header)
        if header_date is None:
            raise ValueError
        header_mtime = mktime_tz(header_date)
        if mtime > header_mtime:
            raise ValueError
    except (ValueError, OverflowError):
        return True
    return False
