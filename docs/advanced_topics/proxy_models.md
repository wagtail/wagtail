# Proxy models

[Proxy models](https://docs.djangoproject.com/en/stable/topics/db/models/#proxy-models) are a way to model polymorphism in Django; where multiple variations of a model share the same fields (defined on a concrete 'parent' model) but differ in other ways. For example, they might implement one or more model methods differently, or set different values on the class to affect certain behaviours (e.g. `template_name`, `search_fields`, `content_panels`).

## Support in Wagtail

```{versionadded} 7.0```

Proxy models can be used as page models, registered as Snippets, or via a ``ModelViewSet``.

### Showing relevant items in listings

Proxy model instance data is stored in the database table for the _parent_ model, instead of a separate one. While this makes retrieving data for all instances more efficient (as fewer 'inner joins' are needed at the database level), this also creates a problem:

**There is no built-in way to 'cast' previously saved data back into instances of the original type.**

The (often surprising) default behaviour for proxy model managers is:

 **No matter which model manager you request a queryset from, the result will include ALL objects that share the same parent model.**

The practical impact of this for editors is:

**No matter which listing view they visit to manage instances of a specific proxy model, they will see items for all other proxy models that share the same parent model.**

While the `Page` model comes with a built-in solution to this problem, for other proxy models, you'll need to implement your own solution, or use a third-party package like [django-polymorphic](https://django-polymorphic.readthedocs.io/) to help.

If you intend for the model data to be managed within Wagtail, at the **very least**, you'll want to implement custom managers so that listings show only the relevant items for each model.

### Permission management and enforcement

For non-page models, permission management and enforcement for proxy models works as it does for models in Django's admin interface:

- Each proxy model has its own set of permissions, each of which can be assigned separately via Wagtail's group management interface.
- When attempting to list, add, edit or delete a proxy model instance, the editor is checked for the relevant 'proxy model specific' permission. Any permissions on the parent model are ignored.

### Compatibility with other features

For subclasses of `wagtail.search.index.Indexed`, it should be possible to customise `search_fields` for each proxy model in the same way you would for a concrete model. However, this might not be supported for all search backends (e.g. default 'database' backend).

## Are proxy models the right choice?

Proxy models are the perfect solution to some problems, but they come with their own unique quirks and limitations, and often require more custom code than alternative options. If either of the following are true, you should consider using multi-table inheritance instead:

- You are unsure whether variations will always share the same model fields.
- You are planning to add fields to the parent model for the sake of one or two variations, but which are irrelevant to others.

**Remember**: Flexibility and maintainability are often more important than raw performance. There may well be other ways to improve general performance (e.g. caching).
