from __future__ import absolute_import, unicode_literals

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy

from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import CollectionForm
from wagtail.wagtailadmin.navigation import get_explorable_root_collection
from wagtail.wagtailadmin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Collection
from wagtail.wagtailcore.permissions import collection_permission_policy


class Index(IndexView):
    permission_policy = collection_permission_policy
    model = Collection
    context_object_name = 'collections'
    template_name = 'wagtailadmin/collections/index.html'
    add_url_name = 'wagtailadmin_collections:add'
    add_item_label = ugettext_lazy("Add a collection")
    header_icon = 'folder-open-1'

    def __init__(self):
        super(Index, self).__init__()
        self.parent_collection = None

    @property
    def page_title(self):
        if not self.parent_collection:
            return ugettext_lazy("Collections")
        return ugettext_lazy(self.parent_collection.name)

    def get_queryset(self):
        if not self.parent_collection:
            # Find the root collection that the user has access to
            self.parent_collection = get_explorable_root_collection(self.request.user)

        return self.parent_collection.get_children()

    def get_context(self):
        context = super(Index, self).get_context()
        context.update({
            'parent_collection': self.parent_collection,
            'parent_perms': self.parent_collection.permissions_for_user(self.request.user),
        })
        return context

    def get(self, request, root_id=None):
        if root_id:
            self.parent_collection = get_object_or_404(Collection, pk=root_id)

        context = self.get_context()
        return render(request, self.template_name, context)


class Create(CreateView):
    permission_policy = collection_permission_policy
    form_class = CollectionForm
    page_title = ugettext_lazy("Add collection")
    success_message = ugettext_lazy("Collection '{0}' created.")
    add_url_name = 'wagtailadmin_collections:add_child'
    edit_url_name = 'wagtailadmin_collections:edit'
    header_icon = 'folder-open-1'

    def __init__(self):
        super(Create, self).__init__()
        self._parent_collection = None

    @property
    def index_url_name(self):
        return reverse('wagtailadmin_collections:parent_index', args=(self.parent_collection.pk, ))

    @property
    def parent_collection(self):
        # Convenience method for getting the correct parent collection object, will fallback to
        # using the root collection
        if not self._parent_collection:
            self._parent_collection = Collection.get_first_root_node()
        return self._parent_collection

    @parent_collection.setter
    def parent_collection(self, parent_id):
        # Take the parent collection id and get the collection object
        self._parent_collection = get_object_or_404(Collection, pk=parent_id)

    def save_instance(self):
        # Always create new collections as children of root
        instance = self.form.save(commit=False)
        self.parent_collection.add_child(instance=instance)
        return instance

    def post(self, request, parent_id=None):
        if parent_id:
            self.parent_collection = parent_id
        return super(Create, self).post(request=request)

    def get(self, request, parent_id=None):
        if parent_id:
            self.parent_collection = parent_id
        return super(Create, self).get(request=request)

    def get_add_url(self):
        return reverse(self.add_url_name, args=(self.parent_collection.pk, ))


class Edit(EditView):
    permission_policy = collection_permission_policy
    model = Collection
    form_class = CollectionForm
    success_message = ugettext_lazy("Collection '{0}' updated.")
    error_message = ugettext_lazy("The collection could not be saved due to errors.")
    delete_item_label = ugettext_lazy("Delete collection")
    edit_url_name = 'wagtailadmin_collections:edit'
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    context_object_name = 'collection'
    header_icon = 'folder-open-1'

    def get_queryset(self):
        # Return all collections except the root collection to prevent it from being editable
        return Collection.objects.exclude(pk=Collection.get_first_root_node().pk)


class Delete(DeleteView):
    permission_policy = collection_permission_policy
    model = Collection
    success_message = ugettext_lazy("Collection '{0}' deleted.")
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    page_title = ugettext_lazy("Delete collection")
    confirmation_message = ugettext_lazy("Are you sure you want to delete this collection?")
    header_icon = 'folder-open-1'

    def get_queryset(self):
        # Return all collections except the root collection to prevent it from being editable
        return Collection.objects.exclude(pk=Collection.get_first_root_node().pk)

    def get_collection_contents(self):
        # TODO: Need to get the contents for any collections nested under the one being deleted.
        collection_contents = [
            hook(self.instance)
            for hook in hooks.get_hooks('describe_collection_contents')
        ]

        # filter out any hook responses that report that the collection is empty
        # (by returning None, or a dict with 'count': 0)
        def is_nonempty(item_type):
            return item_type and item_type['count'] > 0

        return list(filter(is_nonempty, collection_contents))

    def get_context(self):
        context = super(Delete, self).get_context()
        collection_contents = self.get_collection_contents()

        if collection_contents:
            # collection is non-empty; render the 'not allowed to delete' response
            self.template_name = 'wagtailadmin/collections/delete_not_empty.html'
            context['collection_contents'] = collection_contents

        return context

    def post(self, request, instance_id):
        self.instance = get_object_or_404(self.get_queryset(), id=instance_id)
        collection_contents = self.get_collection_contents()

        if collection_contents:
            # collection is non-empty; refuse to delete it
            return HttpResponseForbidden()

        self.instance.delete()
        messages.success(request, self.success_message.format(self.instance))
        return redirect(self.index_url_name)
