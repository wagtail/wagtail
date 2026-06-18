from django.core.checks import Warning, register


@register("search")
def page_search_fields_check(app_configs, **kwargs):
    """Checks each page model with search_fields to core fields are included"""
    from wagtail.models import Page, get_page_models

    page_models = get_page_models()
    errors = []

    for cls in page_models:
        # Don't check models where indexing has been explicitly disabled
        if not cls.search_fields:
            continue
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


@register("models")
def clusterable_model_field_check(app_configs, **kwargs):
    """
    Checks that models inheriting from both ClusterableModel and RevisionMixin
    use ClusterTaggableManager and ParentalManyToManyField instead of their
    standard counterparts.

    Uses local_many_to_many to only check fields declared directly on the model,
    avoiding duplicate warnings for fields inherited from parent classes.
    TaggableManager (a RelatedField, not a ManyToManyField subclass) is also
    included in local_many_to_many by Django.
    """
    from django.apps import apps
    from django.db.models import ManyToManyField
    from modelcluster.contrib.taggit import ClusterTaggableManager
    from modelcluster.fields import ParentalManyToManyField
    from modelcluster.models import ClusterableModel
    from taggit.managers import TaggableManager

    from wagtail.models import RevisionMixin

    errors = []

    for model in apps.get_models():
        if not (
            issubclass(model, ClusterableModel) and issubclass(model, RevisionMixin)
        ):
            continue

        # local_many_to_many returns fields declared directly on the model,
        # including TaggableManager instances. This avoids duplicate warnings
        # when child models inherit a problematic field from a parent.
        for field in model._meta.local_many_to_many:
            if isinstance(field, TaggableManager) and not isinstance(
                field, ClusterTaggableManager
            ):
                errors.append(
                    Warning(
                        "{model}.{field} uses TaggableManager, which does not work with "
                        "revision-enabled ClusterableModels.".format(
                            model=model.__name__, field=field.name
                        ),
                        hint=(
                            "Replace TaggableManager with ClusterTaggableManager from "
                            "modelcluster.contrib.taggit so that tag data is included in revisions."
                        ),
                        obj=model,
                        id="wagtailcore.W003",
                    )
                )
            elif isinstance(field, ManyToManyField) and not isinstance(
                field, ParentalManyToManyField
            ):
                errors.append(
                    Warning(
                        "{model}.{field} uses ManyToManyField, which does not work with "
                        "revision-enabled ClusterableModels.".format(
                            model=model.__name__, field=field.name
                        ),
                        hint=(
                            "Replace ManyToManyField with ParentalManyToManyField from "
                            "modelcluster.fields so that related data is included in revisions."
                        ),
                        obj=model,
                        id="wagtailcore.W002",
                    )
                )

    return errors
