from wagtail.api import APIField
from wagtail.api.v3.registry import ContentTypeRegistration, registry
from wagtail.api.v3.schemas import create_generator, patch_generator, read_generator
from wagtail.models import DraftStateMixin
from wagtail.snippets.api.v3.schemas import (
    PUBLISH_ACTION_META_FIELD,
    BaseSnippetCreateSchema,
    BaseSnippetSchema,
    BaseSnippetUpdateSchema,
)
from wagtail.snippets.models import get_snippet_models


def register_content_types() -> None:
    """Register a content type for ``snippets`` and each snippet model."""
    for model in get_snippet_models():
        # Skip models that don't have any API fields defined, since they cannot
        # be meaningfully used.
        if not APIField.get_fields_for_model(model):
            continue

        # DraftStateMixin models get an extra meta.action field on create/
        # update, letting a request publish the revision in the same call.
        extra_meta_fields = None
        if issubclass(model, DraftStateMixin):
            extra_meta_fields = PUBLISH_ACTION_META_FIELD

        registry.register(
            ContentTypeRegistration(
                name=model._meta.label,
                label=str(model._meta.verbose_name),
                read_schema=read_generator.generate_schema(
                    model,
                    base_class=BaseSnippetSchema,
                ),
                create_schema=create_generator.generate_schema(
                    model,
                    base_class=BaseSnippetCreateSchema,
                    extra_meta_fields=extra_meta_fields,
                ),
                patch_schema=patch_generator.generate_schema(
                    model,
                    base_class=BaseSnippetUpdateSchema,
                    extra_meta_fields=extra_meta_fields,
                ),
            )
        )
