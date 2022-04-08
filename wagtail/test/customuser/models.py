from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

# make sure we can import wagtail.admin.auth here without triggering a circular import
# (which is easily done because it's dealing with django.contrib.auth views which depend
# on the user model)
from wagtail.admin.auth import permission_denied  # noqa
from wagtail.admin.panels import FieldPanel

from .fields import ConvertedValueField


class CustomUserManager(BaseUserManager):
    def _create_user(
        self,
        username,
        email,
        password,
        is_staff,
        is_superuser,
        is_active=True,
        **extra_fields,
    ):
        """
        Creates and saves a User with the given username, email and password.
        """
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            is_staff=is_staff,
            is_active=is_active,
            is_superuser=is_superuser,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        return self._create_user(
            username, email, password, False, False, **extra_fields
        )

    def create_superuser(self, username, email, password, **extra_fields):
        return self._create_user(username, email, password, True, True, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    identifier = ConvertedValueField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=255, blank=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=100, blank=True)
    attachment = models.FileField(blank=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = CustomUserManager()

    def get_full_name(self):
        return self.first_name + " " + self.last_name

    def get_short_name(self):
        return self.first_name

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
    ]
