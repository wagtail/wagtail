Pages
=====

Wagtail requires a little careful setup to define the types of content that you want to present through your website. The basic unit of content in Wagtail is the ``Page``, and all of your page-level content will inherit basic webpage-related properties from it. But for the most part, you will be defining content yourself, through the construction of Django models using Wagtail's ``Page`` as a base.

Wagtail organizes content created from your models in a tree, which can have any structure and combination of model objects in it. Wagtail doesn't prescribe ways to organize and interrelate your content, but here we've sketched out some strategies for organizing your models.

The presentation of your content, the actual webpages, includes the normal use of the Django template system. We'll cover additional functionality that Wagtail provides at the template level later on.


.. toctree::
    :maxdepth: 2

    theory
    creating_pages
    writing_templates
    model_recipes
    editing_api
    streamfield
    sites
    advanced_topics/queryset_methods
    advanced_topics/private_pages
    model_reference
