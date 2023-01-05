from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.utils.translation import gettext_lazy as _


class WagtailSnippetsAppConfig(AppConfig):
    name = "wagtail.snippets"
    label = "wagtailsnippets"
    verbose_name = _("Wagtail snippets")

    def ready(self):
        from .models import create_extra_permissions, register_deferred_snippets

        # Register all snippets for which register_snippet was called up to this point -
        # these registrations had to be deferred as we could not guarantee that models were
        # fully loaded at that point (but now they are).
        register_deferred_snippets()

        # Models with certain mixins, e.g. DraftStateMixin, may require extra permissions
        # in the admin. We need to make sure these are available without having to be
        # created manually.
        # Django also uses post_migrate signal to create permissions for models based on
        # the model's Meta options:
        # https://github.com/django/django/blob/64b3c413da011f55469165256261f406a277e822/django/contrib/auth/apps.py#L19-L22
        # However, we cannot put the extra permissions in the model mixin's Meta class,
        # as we do not know the concrete model's name. Thus, we use our own signal handler
        # to create the extra permissions.
        post_migrate.connect(create_extra_permissions, sender=self)
