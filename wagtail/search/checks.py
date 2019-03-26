from django.core.checks import Warning, register


@register('search')
def page_search_fields_check(app_configs, **kwargs):
    """Checks each page model with search_fields to ensure core fields are included"""
    from wagtail.core.models import get_page_models, Page

    page_models = get_page_models()
    errors = []

    for cls in page_models:
        if not all(field in cls.search_fields for field in Page.search_fields_core):
            errors.append(
                Warning(
                    'Core page fields missing in `search_fields`',
                    hint=' '.join([
                        'Ensure that {} extends the Page model search fields',
                        '`search_fields = Page.search_fields + [...]`'
                    ]).format(cls.__name__),
                    obj=cls,
                    id='wagtailsearch.W001'
                ))

    return errors
