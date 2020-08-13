from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, Group, Permission, PermissionsMixin)
from django.db import models


class EmailUserManager(BaseUserManager):
    def _create_user(self, email, password,
                     is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        return self._create_user(email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True,
                                 **extra_fields)


class EmailUser(AbstractBaseUser):
    # Cant inherit from PermissionsMixin because of clashes with
    # groups/user_permissions related_names.
    email = models.EmailField(max_length=255, unique=True)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    is_superuser = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, related_name='+', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='+', blank=True)

    USERNAME_FIELD = 'email'

    objects = EmailUserManager()

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_short_name(self):
        return self.first_name


methods = ['get_group_permissions', 'get_all_permissions', 'has_perm',
           'has_perms', 'has_module_perms']
for method in methods:
    func = getattr(PermissionsMixin, method)
    setattr(EmailUser, method, func)
