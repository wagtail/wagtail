from django.utils.http import is_safe_url


def get_valid_next_url_from_request(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if not next_url or not is_safe_url(url=next_url, allowed_hosts={request.get_host()}):
        return ''
    return next_url
