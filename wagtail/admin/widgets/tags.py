import json
from warnings import warn

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from taggit.forms import TagWidget
from taggit.models import Tag

from wagtail.utils.deprecation import RemovedInWagtail80Warning


class AdminTagWidget(TagWidget):
    template_name = "wagtailadmin/widgets/tag_widget.html"

    def __init__(self, *args, **kwargs):
        self.tag_model = kwargs.pop("tag_model", Tag)
        # free_tagging = None means defer to the tag model's setting
        self.free_tagging = kwargs.pop("free_tagging", None)

        default_attrs = {"data-controller": "w-tag"}
        attrs = kwargs.get("attrs")
        if attrs:
            default_attrs.update(attrs)
        kwargs["attrs"] = default_attrs

        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        if self.tag_model == Tag:
            autocomplete_url = reverse("wagtailadmin_tag_autocomplete")
        else:
            autocomplete_url = reverse(
                "wagtailadmin_tag_model_autocomplete",
                args=(self.tag_model._meta.app_label, self.tag_model._meta.model_name),
            )

        if self.free_tagging is None:
            free_tagging = getattr(self.tag_model, "free_tagging", True)
        else:
            free_tagging = self.free_tagging

        if hasattr(settings, "TAG_SPACES_ALLOWED"):
            warn(
                "The setting 'TAG_SPACES_ALLOWED' is deprecated. "
                "Please use 'WAGTAIL_TAG_SPACES_ALLOWED' instead.",
                RemovedInWagtail80Warning,
            )
        tag_spaces_allowed = getattr(
            settings,
            "WAGTAIL_TAG_SPACES_ALLOWED",
            # RemovedInWagtail80Warning: Remove fallback to deprecated setting
            getattr(settings, "TAG_SPACES_ALLOWED", True),
        )

        if tag_spaces_allowed:
            help_text = _(
                'Multi-word tags with spaces will automatically be enclosed in double quotes (").'
            )
        else:
            help_text = _("Tags can only consist of a single word, no spaces allowed.")

        if hasattr(settings, "TAG_LIMIT"):
            warn(
                "The setting 'TAG_LIMIT' is deprecated. "
                "Please use 'WAGTAIL_TAG_LIMIT' instead.",
                RemovedInWagtail80Warning,
            )
        tag_limit = getattr(
            settings,
            "WAGTAIL_TAG_LIMIT",
            # RemovedInWagtail80Warning: Remove fallback to deprecated setting
            getattr(settings, "TAG_LIMIT", None),
        )

        context["widget"]["help_text"] = help_text
        context["widget"]["attrs"]["data-w-tag-delay-value"] = 200
        context["widget"]["attrs"]["data-w-tag-url-value"] = autocomplete_url
        context["widget"]["attrs"]["data-w-tag-options-value"] = json.dumps(
            {
                "allowSpaces": tag_spaces_allowed,
                "tagLimit": tag_limit,
                "autocompleteOnly": not free_tagging,
            }
        )

        return context
