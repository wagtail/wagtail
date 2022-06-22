# Multi-site, multi-instance and multi-tenancy

This page gives background information on how to run multiple Wagtail sites (with the same source code).

```{contents}
---
local:
---
```

## Multi-site

Multi-site is a Wagtail project configuration where content creators go into a single admin interface and manage the content of multiple websites. Permission to manage specific content, and restricting access to other content, is possible to some extent.

Multi-site configuration is a single code base, on a single server, connecting to a single database. Media is stored in a single media root directory. Content can be shared between sites.

Wagtail supports multi-site out of the box: Wagtail comes with a [site model](wagtail.models.Site). The site model contains a hostname, port, and root page field. When a URL is requested, the request comes in, the domain name and port are taken from the request object to look up the correct site object. The root page is used as starting point to resolve the URL and serve the correct page.

Wagtail also comes with [site settings](settings). _Site settings_ are 'singletons' that let you store additional information on a site. For example, social media settings, a field to upload a logo, or a choice field to select a theme.

Model objects can be linked to a site by placing a foreign key field on the model pointing to the site object. A request object can be used to look up the current site. This way, content belonging to a specific site can be served.

User, groups, and permissions can be configured in such a way that content creators can only manage the pages, images, and documents of a specific site. Wagtail can have multiple _site objects_ and multiple _page trees_. Permissions can be linked to a specific page tree or a subsection thereof. Collections are used to categorize images and documents. A collection can be restricted to users who are in a specific group.

Some projects require content editors to have permissions on specific sites and restrict access to other sites. Splitting _all_ content per site and guaranteeing that no content 'leaks' is difficult to realize in a multi-site project. If you require full separation of content, then multi-instance might be a better fit...

## Multi-instance

Multi-instance is a Wagtail project configuration where a single set of project files is used by multiple websites. Each website has its own settings file, and a dedicated database and media directory. Each website runs in its own server process. This guarantees the _total separation_ of _all content_.

Assume the domains a.com and b.com. Settings files can be `base.py`, `acom.py`, and `bcom.py`. The base settings will contain all settings like normal. The contents of site-specific settings override the base settings:

```python
# settings/acom.py

from base import \* # noqa

ALLOWED_HOSTS = ['a.com']
DATABASES["NAME"] = "acom"
DATABASES["PASSWORD"] = "password-for-acom"
MEDIA_DIR = BASE_DIR / "acom-media"
```

Each site can be started with its own settings file. In development `./manage.py runserver --settings settings.acom`.
In production, for example with uWSGI, specify the correct settings with `env = DJANGO_SETTINGS_MODULE=settings.acom`.

Because each site has its own database and media folder, nothing can 'leak' to another site. But this also means that content cannot be shared between sites as one can do when using the multi-site option.

In this configuration, multiple sites share the same, single set of project files. Deployment would update the single set of project files and reload each instance.

This multi-instance configuration isn't that different from deploying the project code several times. However, having a single set of project files, and only differentiate with settings files, is the closest Wagtail can get to true multi-tenancy. Every site is identical, content is separated, including user management. 'Adding a new tenant' is adding a new settings file and running a new instance.

In a multi-instance configuration, each instance requires a certain amount of server resources (CPU and memory). That means adding sites will increase server load. This only scales up to a certain point.

## Multi-tenancy

Multi-tenancy is a project configuration in which a single instance of the software serves multiple tenants. A tenant is a group of users who have access and permission to a single site. Multitenant software is designed to provide every tenant its configuration, data, and user management.

Wagtail supports _multi-site_, where user management and content are shared. Wagtail can run _multi-instance_ where there is full separation of content at the cost of running multiple instances. Multi-tenancy combines the best of both worlds: a single instance, and the full separation of content per site and user management.

Wagtail does not support full multi-tenancy at this moment. But it is on our radar, we would like to improve Wagtail to add multi-tenancy - while still supporting the existing multi-site option. If you have ideas or like to contribute, join us on [Slack](slack) in the multi-tenancy channel.

Wagtail currently has the following features to support multi-tenancy:

-   A Site model mapping a hostname to a root page
-   Permissions to allow groups of users to manage:

    -   arbitrary sections of the page tree
    -   sections of the collection tree (coming soon)
    -   one or more collections of documents and images

-   The page API is automatically scoped to the host used for the request

But several features do not currently support multi-tenancy:

-   Snippets are global pieces of content so not suitable for multi-tenancy but any model that can be registered as a snippet can also be managed via the Wagtail model admin. You can add a site_id to the model and then use the model admin get_queryset method to determine which site can manage each object. The built-in snippet choosers can be replaced by [modelchooser](https://pypi.org/project/wagtail-modelchooser/) that allows filtering the queryset to restrict which sites may display which objects.
-   Site, site setting, user, and group management. At the moment, your best bet is to only allow superusers to manage these objects.
-   Workflows and workflow tasks
-   Site history
-   Redirects

Permission configuration for built-in models like Sites, Site settings and Users is not site-specific, so any user with permission to edit a single entry can edit them all. This limitation can be mostly circumvented by only allowing superusers to manage these models.

Python, Django, and Wagtail allow you to override, extend and customise functionality. Here are some ideas that may help you create a multi-tenancy solution for your site:

-   Django allows to override templates, this also works in the Wagtail admin.
-   A custom user model can be used to link users to a specific site.
-   Custom admin views can provide more restrictive user management.

We welcome interested members of the Wagtail community to contribute code and ideas.
