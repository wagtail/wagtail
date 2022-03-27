from django.urls import include, path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _

import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import hooks
from wagtail.embeds import urls
from wagtail.embeds.rich_text import MediaEmbedHandler
from wagtail.embeds.rich_text.contentstate import ContentstateMediaConversionRule
from wagtail.embeds.rich_text.editor_html import EditorHTMLEmbedConversionRule


@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("embeds/", include(urls, namespace="wagtailembeds")),
    ]


@hooks.register("insert_editor_js")
def editor_js():
    return format_html(
        """
            <script>
                window.chooserUrls.embedsChooser = '{0}';
            </script>
        """,
        reverse("wagtailembeds:chooser"),
    )


@hooks.register("register_rich_text_features")
def register_embed_feature(features):
    # define a handler for converting <embed embedtype="media"> tags into frontend HTML
    features.register_embed_type(MediaEmbedHandler)

    # define how to convert between editorhtml's representation of embeds and
    # the database representation
    features.register_converter_rule(
        "editorhtml", "embed", EditorHTMLEmbedConversionRule
    )

    # define a draftail plugin to use when the 'embed' feature is active
    features.register_editor_plugin(
        "draftail",
        "embed",
        draftail_features.EntityFeature(
            {
                "type": "EMBED",
                "icon": "media",
                "description": _("Embed"),
            },
            js=["wagtailembeds/js/embed-chooser-modal.js"],
        ),
    )

    # define how to convert between contentstate's representation of embeds and
    # the database representation-
    features.register_converter_rule(
        "contentstate", "embed", ContentstateMediaConversionRule
    )

    # add 'embed' to the set of on-by-default rich text features
    features.default_features.append("embed")
