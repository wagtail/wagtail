from django.shortcuts import render
from django.views.decorators.cache import cache_control


@cache_control(max_age=3600, private=True)
def sprite(request):
    """We should cache this icon sprite. But the cache doesn't seem to work (because of the development server?)."""
    return render(request, 'wagtailadmin/icons/sprite.svg')
