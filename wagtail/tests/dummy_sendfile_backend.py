from django.http import HttpResponse


def sendfile(request, filename, **kwargs):
    """
    Dummy sendfile backend implementation.
    """
    return HttpResponse('Dummy backend response')
