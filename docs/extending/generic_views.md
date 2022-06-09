Generic views
=============

Wagtail provides a number of generic views for handling common tasks such as creating / editing model instances, and chooser modals. Since these often involve several related views with shared properties (such as the model that we're working with, and its associated icon) Wagtail also implements the concept of a _viewset_, which allows a bundle of views to be defined collectively, and their URLs to be registered with the admin app as a single operation through the `register_admin_viewset` hook.

