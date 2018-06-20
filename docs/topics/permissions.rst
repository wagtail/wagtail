.. _permissions:

===========
Permissions
===========

Wagtail adapts and extends `the Django permission system <https://docs.djangoproject.com/en/stable/topics/auth/default/#topic-authorization>`_ to cater for the needs of website content creation, such as moderation workflows, and multiple teams working on different areas of a site (or multiple sites within the same Wagtail installation). Permissions can be configured through the 'Groups' area of the Wagtail admin interface, under 'Settings'.


Page permissions
----------------

Permissions can be attached at any point in the page tree, and propagate down the tree. For example, if a site had the page tree::

    MegaCorp/
        About us
        Offices/
            UK
            France
            Germany

then a group with 'edit' permissions on the 'Offices' page would automatically receive the ability to edit the 'UK', 'France' and 'Germany' pages. Permissions can be set globally for the entire tree by assigning them on the 'root' page - since all pages must exist underneath the root node, and the root cannot be deleted, this permission will cover all pages that exist now and in future.

Whenever a user creates a page through the Wagtail admin, that user is designated as the owner of that page. Any user with 'add' permission has the ability to edit pages they own, as well as adding new ones. This is in recognition of the fact that creating pages is typically an iterative process involving creating a number of draft versions - giving a user the ability to create a draft but not letting them subsequently edit it would not be very useful. Ability to edit a page also implies the ability to delete it; unlike Django's standard permission model, there is no distinct 'delete' permission.

The full set of available permission types is as follows:

* **Add** - grants the ability to create new subpages underneath this page (provided the page model permits this - see :ref:`page_type_business_rules`), and to edit and delete pages owned by the current user. Published pages cannot be deleted unless the user also has 'publish' permission.
* **Edit** - grants the ability to edit and delete this page, and any pages underneath it, regardless of ownership. A user with only 'edit' permission may not create new pages, only edit existing ones. Published pages cannot be deleted unless the user also has 'publish' permission.
* **Publish** - grants the ability to publish and unpublish this page and/or its children. A user without publish permission cannot directly make changes that are visible to visitors of the website; instead, they must submit their changes for moderation (which will send a notification to users with publish permission). Publish permission is independent of edit permission; a user with only publish permission will not be able to make any edits of their own.
* **Bulk delete** - allows a user to delete pages that have descendants, in a single operation. Without this permission, a user has to delete the descendant pages individually before deleting the parent. This is a safeguard against accidental deletion. This permission must be used in conjunction with 'add' / 'edit' permission, as it does not provide any deletion rights of its own; it only provides a 'shortcut' for the permissions the user has already. For example, a user with just 'add' and 'bulk delete' permissions will only be able to bulk-delete if all the affected pages are owned by that user, and are unpublished.
* **Lock** - grants the ability to lock or unlock this page (and any pages underneath it) for editing, preventing users from making any further edits to it.

Drafts can be viewed only if the user has either Edit or Publish permission.


.. _image_document_permissions:

Image / document permissions
----------------------------

The permission rules for images and documents work on a similar basis to pages. Images and documents are considered to be 'owned' by the user who uploaded them; a user with 'add' permission also has the ability to edit items they own; and deletion is considered equivalent to editing rather than having a specific permission type.

Access to specific sets of images and documents can be controlled by setting up *collections*. By default all images and documents belong to the 'root' collection, but new collections can be created through the Settings -> Collections area of the admin interface. Permissions set on 'root' apply to all collections, so a user with 'edit' permission for images on root can edit all images; permissions set on other collections apply to that collection only.
