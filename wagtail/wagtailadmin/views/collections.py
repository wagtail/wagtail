from __future__ import absolute_import, unicode_literals

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import ugettext_lazy
from django.views.generic.base import View

from wagtail.utils.pagination import paginate
from wagtail.wagtailadmin import messages
from wagtail.wagtailadmin.forms import CollectionForm, SearchForm
from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.navigation import get_explorable_root_collection
from wagtail.wagtailadmin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.models import Collection


class CollectionPermissionMixin(object):

    def check_permissions(self, collection_perms):
        """All classes using this mixin must implement this function.

        Called for every dispatch event to check if the user has access to the collection view.

        :param wagtail.wagtailcore.models.CollectionPermissionTester collection_perms: The collection permission tester
            object used to determine the level of access the user should be given.
        """
        raise NotImplementedError

    def dispatch(self, request, instance_id, *args, **kwargs):
        collection = get_object_or_404(Collection, pk=instance_id)
        collection_perms = collection.permissions_for_user(request.user)
        if not self.check_permissions(collection_perms):
            raise PermissionDenied
        return super(CollectionPermissionMixin, self).dispatch(request, instance_id, *args, **kwargs)


class Index(IndexView):
    model = Collection
    context_object_name = 'collections'
    template_name = 'wagtailadmin/collections/index.html'
    add_url_name = 'wagtailadmin_collections:add'
    add_item_label = ugettext_lazy("Add a collection")
    header_icon = 'folder-open-1'

    def __init__(self):
        super(Index, self).__init__()
        self.parent_collection = None
        self.is_searching = False

    @property
    def page_title(self):
        if not self.parent_collection:
            return ugettext_lazy("Collections")
        return ugettext_lazy(self.parent_collection.name)

    def get_queryset(self):
        search = SearchForm(self.request.GET)

        if search.is_valid() and search.cleaned_data['q']:
            self.is_searching = True
            return Collection.objects.filter(name__icontains=search.cleaned_data['q'])
        else:
            if not self.parent_collection:
                # Find the root collection that the user has access to
                self.parent_collection = get_explorable_root_collection(self.request.user)

            return self.parent_collection.get_children()

    def get_context(self):
        context = super(Index, self).get_context()
        # Turn the queryset of collections into a Paginator
        paginator, collections = paginate(self.request, context[self.context_object_name], per_page=50)

        context.update({
            'collections': collections,
            'paginator': paginator,
            'search_form': SearchForm(),
        })

        # Chooser search results don't need this
        if not self.is_searching:
            context.update({
                'parent_collection': self.parent_collection,
                'parent_perms': self.parent_collection.permissions_for_user(self.request.user),
            })

        return context

    def get(self, request, root_id=None):
        if root_id:
            self.parent_collection = get_object_or_404(Collection, pk=root_id)
        context = self.get_context()

        # All requests originating from the collection chooser will a `modal` query param.
        if request.GET.get('modal'):
            # Handle searching from the chooser
            if request.GET.get('results_only'):
                return render(
                    request,
                    template_name='wagtailadmin/chooser/_collection_search_results.html',
                    context=context,
                )

            # Render the collection chooser modal
            return render_modal_workflow(
                request,
                'wagtailadmin/chooser/collection_browse.html', 'wagtailadmin/chooser/collection_browse.js',
                context,
            )

        # Render the regular listing page
        return render(request, self.template_name, context)


class Create(CollectionPermissionMixin, CreateView):
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

    def check_permissions(self, collection_perms):
        return collection_perms.can_add()

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


class Edit(CollectionPermissionMixin, EditView):
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

    @property
    def index_url_name(self):
        # Redirect to the index view of the parent collection
        return reverse('wagtailadmin_collections:parent_index', args=(self.instance.get_parent().pk, ))

    def check_permissions(self, collection_perms):
        return collection_perms.can_edit()

    def get_queryset(self):
        # Return all collections except the root collection to prevent it from being editable
        return Collection.objects.exclude(pk=Collection.get_first_root_node().pk)


class Delete(CollectionPermissionMixin, DeleteView):
    model = Collection
    success_message = ugettext_lazy("Collection '{0}' deleted.")
    delete_url_name = 'wagtailadmin_collections:delete'
    page_title = ugettext_lazy("Delete collection")
    confirmation_message = ugettext_lazy("Are you sure you want to delete this collection?")
    header_icon = 'folder-open-1'

    @property
    def index_url_name(self):
        # Redirect to the index view of the parent collection
        return reverse('wagtailadmin_collections:parent_index', args=(self.instance.get_parent().pk, ))

    def check_permissions(self, collection_perms):
        return collection_perms.can_delete()

    def get_queryset(self):
        # Return all collections except the root collection to prevent it from being editable
        return Collection.objects.exclude(pk=Collection.get_first_root_node().pk)

    def get_collection_contents(self, collection):
        collection_contents = [
            hook(collection)
            for hook in hooks.get_hooks('describe_collection_contents')
        ]

        # filter out any hook responses that report that the collection is empty
        # (by returning None, or a dict with 'count': 0)
        def is_nonempty(item_type):
            return item_type and item_type['count'] > 0

        return list(filter(is_nonempty, collection_contents))

    def get_children_collection_contents(self):
        """Get the content information for every collection nested under the collection to be deleted.

        The format for the content under each of the children collections is:

        .. code-block:: python

            [
                {
                    'collection': <wagtail.wagtailcore.models.Collection>,  # the child collection
                    'items': [{}, ],  # list of dictionaries returned from the 'describe_collection_contents' hook
                },
                ...
            ]

        :returns: A list of dictionaries for every child collection containing any content. Will return an empty list
            if none of its descendants contain any content.
        """
        collection_to_delete = self.instance
        descendant_contents = []
        # If this collection contains any children collections, then we only want to delete it
        # if none of its children have any contents.
        if not collection_to_delete.is_leaf():
            descendant_collections = collection_to_delete.get_descendants()
            for collection in descendant_collections:
                # Check if the collection has anything in it
                contents = self.get_collection_contents(collection)
                if contents:
                    descendant_contents.append({
                        'collection': collection,
                        'items': contents,
                    })

        return descendant_contents

    def get_context(self):
        context = super(Delete, self).get_context()
        collection_contents = self.get_collection_contents(self.instance)
        descendant_contents = self.get_children_collection_contents()
        context['descendant_contents'] = descendant_contents

        if collection_contents or descendant_contents:
            # collection is non-empty; render the 'not allowed to delete' response
            self.template_name = 'wagtailadmin/collections/delete_not_empty.html'

        if collection_contents:
            context['collection_contents'] = collection_contents

        return context

    def post(self, request, instance_id):
        self.instance = get_object_or_404(self.get_queryset(), id=instance_id)
        collection_contents = self.get_collection_contents(self.instance)
        descendant_contents = self.get_children_collection_contents()

        if collection_contents or descendant_contents:
            # collection or one of its descendants is non-empty; refuse to delete it
            raise PermissionDenied

        self.instance.delete()
        messages.success(request, self.success_message.format(self.instance))
        return redirect(self.index_url_name)


class Move(View):
    """Allow the user to select which collection they want to move to."""

    def get(self, request, instance_id, viewed_collection_id=None):
        moving_collection = get_object_or_404(Collection, id=instance_id)

        collection_permissions = moving_collection.permissions_for_user(request.user)

        if not collection_permissions.can_move():
            raise PermissionDenied

        if not viewed_collection_id:
            # Find the root collection that the user has access to
            viewed_collection = get_explorable_root_collection(request.user)
        else:
            viewed_collection = get_object_or_404(Collection, id=viewed_collection_id)

        viewed_collection.can_choose = collection_permissions.can_move_to(viewed_collection)

        paginator, collections = paginate(request, viewed_collection.get_children(), per_page=50)

        for collection in collections:
            collection.can_choose = collection_permissions.can_move_to(collection)

        return render(
            request,
            'wagtailadmin/collections/move.html',
            {
                'moving_collection': moving_collection,
                'parent_collection': viewed_collection,
                'collections': collections,
                'paginator': paginator,
            }
        )


class MoveConfirm(View):
    """Confirm that the user wants to move the collection. If so, move the collection in the tree."""

    def get(self, request, instance_id, destination_id):
        moving_collection = get_object_or_404(Collection, id=instance_id)
        destination_collection = get_object_or_404(Collection, id=destination_id)

        # Prevent the user from moving the collection somewhere they aren't allowed
        permissions_tester = moving_collection.permissions_for_user(request.user)
        if not permissions_tester.can_move_to(destination_collection):
            raise PermissionDenied

        return render(
            request,
            'wagtailadmin/collections/confirm_move.html',
            {
                'moving_collection': moving_collection,
                'destination_collection': destination_collection
            }
        )

    def post(self, request, instance_id, destination_id):
        moving_collection = get_object_or_404(Collection, id=instance_id)
        destination_collection = get_object_or_404(Collection, id=destination_id)

        # Prevent the user from moving the collection somewhere they aren't allowed
        permissions_tester = moving_collection.permissions_for_user(request.user)
        if not permissions_tester.can_move_to(destination_collection):
            raise PermissionDenied

        # Move the collection in the tree
        moving_collection.move(destination_collection, pos='last-child')

        # Notify the user that the move was successful
        messages.success(
            request,
            ugettext_lazy("Collection '{0}' moved.").format(moving_collection.name),
            buttons=[
                messages.button(
                    reverse('wagtailadmin_collections:edit', args=(moving_collection.id,)),
                    ugettext_lazy('Edit')
                )
            ]
        )

        # Redirect to the index view for the collection that was chosen as the destination
        return redirect('wagtailadmin_collections:parent_index', destination_collection.id)
