from django.db.models import Model


class SimpleTranslation(Model):
    """
    SimpleTranslation, dummy model to create the `submit_translation` permission.

    We need this model to be concrete or the following management commands will misbehave:
    - `remove_stale_contenttypes`, will drop the perm
    - `dump_data`, will complain about the missing table
    """
    class Meta:
        default_permissions = []
        permissions = [
            ('submit_translation', "Can submit translations"),
        ]
