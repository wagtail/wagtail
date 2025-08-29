from django.db import models

from wagtail.coreutils import multigetattr


class CommentableJSONField(models.JSONField):
    def get_block_by_content_path(self, value, path_elements):
        try:
            multigetattr(value, ".".join(path_elements))
        except AttributeError:
            return False
        return True
