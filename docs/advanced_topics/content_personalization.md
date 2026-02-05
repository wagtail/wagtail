(content_personalization)=

# Content personalization

Wagtail’s built-in features can go a long way to meet content personalization requirements. We can configure StreamField blocks to only display for specific segments based on the request context. In the editor, preview modes give users a way to review each segment before publishing. Editorial teams can then tailor content for different audience segments within a page and preview how the content appears for each segment.

This supportbs the following use cases:

- Time-aware variants: within specific hours, or for a limited time.
- UTM campaign parameters or referrer segmentation.
- Members-only content for logged-in users or users in specific groups.

For more advanced segmentation or analytics-driven targeting, consider the external [wagtail-personalisation](https://github.com/wagtail/wagtail-personalisation) package. Check out our [Content personalization explainer](https://wagtail.org/content-personalization/) for a birds’ eye view of how core features and the package differ in scope.

## Segmented content block

This example defines a block that stores rich text alongside a segment choice. We use a custom `form_layout` and [`BlockGroup`](wagtail.blocks.BlockGroup) to keep the segment configuration in a collapsed "Settings" section. The `get_context` method of the [block class](wagtail.blocks.Block) reads the request to determine the visitor segment.

Make sure to use [`{% include_block %}`](streamfield_template_rendering) when rendering StreamField content so the block receives the parent context, including the `request` object used by `get_context`.

```python
class SegmentedContentBlock(StructBlock):
    content = RichTextBlock()
    segment = ChoiceBlock(
        choices=[
            ("all", "All visitors"),
            ("logged_in", "Logged-in users"),
            ("anonymous", "Anonymous visitors"),
        ],
        default="all",
    )

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        request = parent_context.get("request") if parent_context else None
        preview = getattr(request, "personalization_preview_segment", None)
        context["is_authenticated"] = (
            preview == "logged_in"
            if preview
            else (request.user.is_authenticated if request else False)
        )
        return context

    class Meta:
        icon = "group"
        template = "blocks/segmented_content_block.html"
        preview_value = {
            "content": "<p>Welcome back! Exclusive content for members.</p>",
            "segment": "logged_in",
        }
        description = "Content targeted to specific audience segments"
        form_layout = BlockGroup(
            children=["content"],
            settings=["segment"],
        )
```

This type of simple segmentation is simple to add to any StructBlock. See [](structblock_custom_order_and_grouping) for details on grouping and ordering StructBlock fields, for scenarios where blocks are already more complex.

### Block template

The template conditionally renders content based on the chosen segment. Here, we also style the block differently for each segment.

```html+django
{% load wagtailcore_tags %}

{% if self.segment == "all" %}
    <div class="segmented-content">{{ self.content|richtext }}</div>
{% elif self.segment == "logged_in" and is_authenticated %}
    <div class="segmented-content segmented-content--logged-in">{{ self.content|richtext }}</div>
{% elif self.segment == "anonymous" and not is_authenticated %}
    <div class="segmented-content segmented-content--anonymous">{{ self.content|richtext }}</div>
{% endif %}
```

## Previewing segments in the admin

You can use [preview modes](wagtail.models.Page.preview_modes) on the page to let editors switch between anonymous and logged-in variants. This mixin stores the selected mode on the request so the block’s `get_context` can apply it during preview.

```python
class PersonalizationPreviewMixin:
    default_preview_mode = "anonymous"
    preview_modes = [
        ("anonymous", _("Anonymous visitor")),
        ("logged_in", _("Logged-in user")),
    ]

    def serve_preview(self, request, mode_name):
        request.personalization_preview_segment = mode_name
        return super().serve_preview(request, mode_name)
```
