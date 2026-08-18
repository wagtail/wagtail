(api_v3_python_api)=

# Python API and extensions

The v3 API is built on reusable Python primitives that you can call directly in tests, fixtures, migration scripts, and management commands, or extend to change how the API behaves for your content models. This page documents those contracts: the operations/actions layer, writable API fields, permission policies, and the current extension points for custom fields and blocks.

```{note}
Most of these objects are imported from `wagtail.actions` and `wagtail.permissions`. They are the same layer the v3 endpoints use, so behaviour such as permissions, revisions, audit logging, hooks, and signals is consistent whether you call them from Python or over the API.
```

## The operations / actions layer

`wagtail.actions` exports a general action system that implements a CMS operation (for example "create this page" or "publish this revision") as a reusable object. The actions centralize the meaningful business behaviour—permission checks, form and model saves, revisions, audit logs, signals, scheduling, and page hooks—so an operation behaves identically no matter which transport invokes it.

The key exports are:

- `BaseAction` — the base class every action subclasses.
- `ActionRegistry` — the registry that maps a model class to the actions available for it.
- `action_registry` — the global, project-wide instance the v3 routers use.

Actions are registered against a model and looked up through the model's inheritance chain, so an action registered on a base class is available to its subclasses, and a more specific subclass registration overrides the base one. Because lookup walks the same inheritance chain that registration targets, both the v3 endpoints and your own Python code resolve the same action for the same model.

### Registering actions

An action is registered against a model class with `action_registry.register()`:

```python
from wagtail.actions import action_registry
from wagtail.actions.base import BaseAction


class MyAction(BaseAction):
    action_name = "do_something"

    def __init__(self, obj, **kwargs):
        super().__init__(obj, **kwargs)
        ...

    def execute(self, **kwargs): ...


action_registry.register(MyModel, MyAction)
```

Two rules apply when registering:

- The action class must subclass `BaseAction` and define a non-empty `action_name`.
- Registration is opt-in: a model only gains the actions explicitly registered for it, either directly or through the `register_actions` hook below.

The v3 endpoints resolve an action by name for a model via the registry's MRO walk, so a more specific class's registration wins over a base class's.

### The `register_actions` hook

Packages can add or replace actions for specific models through the `register_actions` hook, which receives the registry and runs lazily on first lookup:

```python
# wagtail_hooks.py
from wagtail import hooks
from wagtail.actions import action_registry


def register_my_actions(registry):
    registry.register(MyModel, MyAction)


hooks.register("register_actions", register_my_actions)
```

Replacing a default action for a model (for example overriding how a page is published) is done the same way: register your action against that model and it takes precedence for lookups.

### Generic and page actions

The default registrations give every model generic create, edit, and delete actions, add revision reverting to `RevisionMixin` models, draft-state publishing and unpublishing to `DraftStateMixin` models, translation copy to `TranslatableMixin` models, and the full set of page actions to `Page`. These are the same actions the v3 endpoints use, so calling them from Python preserves the same permission checks, revisions, and audit logging.

## Writing API fields

The v3 API uses [`APIField`](apiv2_page_fields_configuration) for both reading and writing. Read fields come from a model's `api_fields`; a field is writable only if it is declared `APIField(name, writable=True)`.

```python
from wagtail.api import APIField


class BlogPage(Page):
    body = StreamField(...)
    published_on = models.DateField(...)

    api_fields = [
        APIField("published_on", writable=True),
    ]
```

The following rules apply:

- A writable field must be a **real, editable model field**. `APIField(name, writable=True)` does not, on its own, create arbitrary ORM write access; the field also needs compatible admin form and edit-handler exposure so the API can bind and validate it.
- Existing DRF serializer fields (for example `ImageRenditionField`) remain readable through a compatibility shim, but they define no input shape and are not writable.
- Computed properties and other non-editable attributes are read-only; they appear in the read schema but have no generated writable shape.

The read and write schemas (see [](api_v3_schema)) reflect this: a field declared writable appears in the `create` and `patch` schemas, while a read-only field appears only in `read`.

## Permission policies

`wagtail.permissions.register_permission_policy()` registers a permission policy for a model class:

```python
from wagtail.permissions import register_permission_policy
from wagtail.permission_policies import ModelPermissionPolicy


register_permission_policy(
    MyModel,
    policy=MyCustomPolicy(),
    exact_class=False,
)
```

If `policy` is omitted, a default `ModelPermissionPolicy` is created for the model. Lookup supports an exact match first, then the nearest ancestor policy, with a fallback to the default model-permission policy. Registration must happen before the model is looked up and cached; a late replacement can raise `ImproperlyConfigured`.

The v3 endpoints rely on this registry for their route and queryset permission checks, so the policy you register for a model is what the API enforces.

## Custom fields and blocks

The runtime StreamField support is driven by the real block and widget APIs, so custom blocks participate through their existing hooks:

- validation through `clean()` and the form widget;
- custom read output through `get_api_representation()`.

There is currently **no public registry to contribute a block-level OpenAPI schema**: the generated schema represents a StreamField as `list[Any]`, and clients cannot discover a block's required types or properties from it (see [](api_v3_streamfield)).

For rich text, the established [`register_rich_text_features`](register_rich_text_features) hook continues to influence a field's feature list. Adding a brand-new API interchange format, however, is not a complete public extension point: format names are hardcoded into the schema types, serializers, converters, and query parameters, so overriding internals alone does not make a new format consistently available.

## Stability caveats

These primitives are exported and clearly intended for reuse, but they are not yet covered by a stable public API contract. Keep the following in mind:

- The action layer is not yet documented as a stable contract. Third-party action replacements must match the constructor arguments each endpoint passes; the registry validates inheritance and `action_name`, but not call signatures.
- Sites and redirects CRUD instantiate the generic action classes directly and bypass the action registry, so replacing actions for those models through the registry does not affect them.
- There is no documented v3 equivalent of the v2 project-created router. Core apps register their routers by mutating the global API during `AppConfig.ready()`. Third-party packages currently need to imitate that pattern, coupling to import order, URL prefixes, and schema-freezing timing.
