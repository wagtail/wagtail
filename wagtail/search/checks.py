from django.core.checks import Warning, register


@register("search")
def page_search_fields_check(app_configs, **kwargs):
    """Checks each page model with search_fields to core fields are included"""
    from wagtail.models import Page, get_page_models

    page_models = get_page_models()
    errors = []

    for cls in page_models:
        # Only checks an initial subset of fields as only need to check some are missing to show the warning
        if not all(field in cls.search_fields for field in Page.search_fields[:10]):
            errors.append(
                Warning(
                    "Core Page fields missing in `search_fields`",
                    hint=" ".join(
                        [
                            "Ensure that {} extends the Page model search fields",
                            "`search_fields = Page.search_fields + [...]`",
                        ]
                    ).format(cls.__name__),
                    obj=cls,
                    id="wagtailsearch.W001",
                )
            )

    return errors
