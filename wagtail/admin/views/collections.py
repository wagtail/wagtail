from django.forms import HiddenInput
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.forms.collections import CollectionForm
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtail.core.permissions import collection_permission_policy


class Index(IndexView):
    permission_policy = collection_permission_policy
    model = Collection
    context_object_name = 'collections'
    template_name = 'wagtailadmin/collections/index.html'
    add_url_name = 'wagtailadmin_collections:add'
    index_url_name = 'wagtailadmin_collections:index'
    page_title = gettext_lazy("Collections")
    add_item_label = gettext_lazy("Add a collection")
    header_icon = 'folder-open-1'

    def get_queryset(self):
        if self.request.user.is_superuser:
            # Only return descendants of the root node, so that the root is not editable
            return Collection.get_first_root_node().get_descendants()
        else:
            return self.permission_policy.collections_user_has_any_permission_for(
                self.request.user, ['add', 'change', 'delete']
            )


class Create(CreateView):
    permission_policy = collection_permission_policy
    form_class = CollectionForm
    page_title = gettext_lazy("Add collection")
    success_message = gettext_lazy("Collection '{0}' created.")
    add_url_name = 'wagtailadmin_collections:add'
    edit_url_name = 'wagtailadmin_collections:edit'
    index_url_name = 'wagtailadmin_collections:index'
    header_icon = 'folder-open-1'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Now filter collections offered in parent field by current user's add permissions
        collections = self.permission_policy.collections_user_has_permission_for(self.request.user, 'add')
        form.fields['parent'].queryset = collections
        return form

    def save_instance(self):
        instance = self.form.save(commit=False)
        parent_pk = self.form.data.get('parent')
        parent = Collection.objects.get(pk=parent_pk)
        parent.add_child(instance=instance)
        return instance


class Edit(EditView):
    permission_policy = collection_permission_policy
    model = Collection
    form_class = CollectionForm
    template_name = 'wagtailadmin/collections/edit.html'
    success_message = gettext_lazy("Collection '{0}' updated.")
    error_message = gettext_lazy("The collection could not be saved due to errors.")
    delete_item_label = gettext_lazy("Delete collection")
    edit_url_name = 'wagtailadmin_collections:edit'
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    context_object_name = 'collection'
    header_icon = 'folder-open-1'

    def get_queryset(self):
        if self.request.user.is_superuser:
            # Only return descendants of the root node, so that the root is not editable
            return Collection.get_first_root_node().get_descendants()
        else:
            return self.permission_policy.collections_user_has_permission_for(
                self.request.user, 'change'
            )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        # If this instance is a collection used to assign permissions for this user,
        # do not let the user move this collection.
        if self.permission_policy.user_has_any_permission_directly_on_instance(
            user, ['add', 'change', 'delete'], form.instance
        ):
            form.fields['parent'].widget = HiddenInput()
        # or if user does not have add permission anywhere, then can't move collection
        elif not self.permission_policy.user_has_permission(user, 'add'):
            form.fields['parent'].widget = HiddenInput()
        else:
            # Filter collections offered in parent field by current user's add permissions
            collections = self.permission_policy.collections_user_has_permission_for(user, 'add')
            form.fields['parent'].queryset = collections
            form.fields['parent'].disabled_queryset = form.instance.get_descendants(inclusive=True)
            form.fields['parent'].empty_label = None

        form.initial['parent'] = form.instance.get_parent().pk
        return form

    def save_instance(self):
        instance = self.form.save()
        parent_pk = self.form.data.get('parent')
        if parent_pk and parent_pk != instance.get_parent().pk:
            instance.move(Collection.objects.get(pk=parent_pk), 'sorted-child')
        return instance

    def form_valid(self, form):
        new_parent_pk = int(form.data.get('parent', 0))
        old_descendants = list(form.instance.get_descendants(
            inclusive=True).values_list('pk', flat=True)
        )
        if new_parent_pk in old_descendants:
            form.add_error('parent', gettext_lazy('Please select another parent'))
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            can_delete = True
        else:
            # Can not delete the collection where the delete permission is assigned
            can_delete = self.permission_policy.descendants_of_collections_with_user_perm(
                self.request.user, ['delete']
            ).filter(pk=self.object.pk).first()
        context['can_delete'] = can_delete
        return context


class Delete(DeleteView):
    permission_policy = collection_permission_policy
    model = Collection
    success_message = gettext_lazy("Collection '{0}' deleted.")
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    page_title = gettext_lazy("Delete collection")
    confirmation_message = gettext_lazy("Are you sure you want to delete this collection?")
    header_icon = 'folder-open-1'

    def get_queryset(self):
        if self.request.user.is_superuser:
            # Only return descendants of the root node, so that the root is not editable
            return Collection.get_first_root_node().get_descendants()
        else:
            return self.permission_policy.descendants_of_collections_with_user_perm(
                self.request.user, ['delete']
            )

    def get_collection_contents(self):
        collection_contents = [
            hook(self.object)
            for hook in hooks.get_hooks('describe_collection_contents')
        ]

        # filter out any hook responses that report that the collection is empty
        # (by returning None, or a dict with 'count': 0)
        def is_nonempty(item_type):
            return item_type and item_type['count'] > 0

        return list(filter(is_nonempty, collection_contents))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection_contents = self.get_collection_contents()

        if collection_contents:
            # collection is non-empty; render the 'not allowed to delete' response
            self.template_name = 'wagtailadmin/collections/delete_not_empty.html'
            context['collection_contents'] = collection_contents

        return context

    def post(self, request, pk):
        self.object = get_object_or_404(self.get_queryset(), id=pk)
        collection_contents = self.get_collection_contents()

        if collection_contents:
            # collection is non-empty; refuse to delete it
            return HttpResponseForbidden()

        self.object.delete()
        messages.success(request, self.success_message.format(self.object))
        return redirect(self.index_url_name)
