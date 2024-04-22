# wagtail.models.collections was moved to wagtail.models.media in #11555;
# this import is retained to accommodate migration files importing from the old location.
# See #11874

from wagtail.models.media import get_root_collection_id  # noqa
