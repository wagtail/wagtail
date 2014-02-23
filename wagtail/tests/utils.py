from django.contrib.auth.models import User


def login(client):
    # Create a user
    User.objects.create_superuser(username='test', email='test@email.com', password='password')

    # Login
    client.login(username='test', password='password')