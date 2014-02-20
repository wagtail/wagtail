from wagtail.wagtailcore.models import Site
from django.contrib.auth.models import User


def get_host():
    return Site.objects.filter(is_default_site=True).first().root_url.split('://')[1]


def login(client):
    # Create a user
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')