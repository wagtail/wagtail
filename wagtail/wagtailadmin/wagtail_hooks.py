from django.contrib.auth.models import Permission
from wagtail.wagtailcore import hooks


def register_permissions():
    return Permission.objects.filter(content_type__app_label='wagtailadmin', codename='access_admin')
hooks.register('register_permissions', register_permissions)
