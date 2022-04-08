from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy

from wagtail import hooks
from wagtail.admin import messages
from wagtail.admin.forms.collections import CollectionForm
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.models import Collection, GroupCollectionPermission
from wagtail.permissions import collection_permission_policy


class Index(IndexView):
    permission_policy = collection_permission_policy
    model = Collection
    context_object_name = "collections"
    template_name = "wagtailadmin/collections/index.html"
    add_url_name = "wagtailadmin_collections:add"
    index_url_name = "wagtailadmin_collections:index"
    page_title = gettext_lazy("Collections")
    add_item_label = gettext_lazy("Add a collection")
    header_icon = "folder-open-1"

    def get_queryset(self):
        return self.permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["add", "change", "delete"]
        ).exclude(depth=1)


class Create(CreateView):
    permission_policy = collection_permission_policy
    form_class = CollectionForm
    page_title = gettext_lazy("Add collection")
    success_message = gettext_lazy("Collection '{0}' created.")
    add_url_name = "wagtailadmin_collections:add"
    edit_url_name = "wagtailadmin_collections:edit"
    index_url_name = "wagtailadmin_collections:index"
    header_icon = "folder-open-1"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Now filter collections offered in parent field by current user's add permissions
        collections = self.permission_policy.instances_user_has_permission_for(
            self.request.user, "add"
        )
        form.fields["parent"].queryset = collections
        return form

    def save_instance(self):
        instance = self.form.save(commit=False)
        parent = self.form.cleaned_data["parent"]
        parent.add_child(instance=instance)
        return instance


class Edit(EditView):
    permission_policy = collection_permission_policy
    model = Collection
    form_class = CollectionForm
    template_name = "wagtailadmin/collections/edit.html"
    success_message = gettext_lazy("Collection '{0}' updated.")
    error_message = gettext_lazy("The collection could not be saved due to errors.")
    delete_item_label = gettext_lazy("Delete collection")
    edit_url_name = "wagtailadmin_collections:edit"
    index_url_name = "wagtailadmin_collections:index"
    delete_url_name = "wagtailadmin_collections:delete"
    context_object_name = "collection"
    header_icon = "folder-open-1"

    def _user_may_move_collection(self, user, instance):
        """
        Is this instance used for assigning GroupCollectionPermissions to the user?
        If so, this user is not allowed do move the collection to a new part of the tree
        """
        if user.is_active and user.is_superuser:
            return True
        else:
            permissions = self.permission_policy._get_permission_objects_for_actions(
                ["add", "edit", "delete"]
            )
            return not GroupCollectionPermission.objects.filter(
                group__user=user,
                permission__in=permissions,
                collection=instance,
            ).exists()

    def get_queryset(self):
        return self.permission_policy.instances_user_has_permission_for(
            self.request.user, "change"
        ).exclude(depth=1)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        # if user does not have add permission anywhere, they can't move a collection
        if not self.permission_policy.user_has_permission(user, "add"):
            form.fields.pop("parent")
        # If this instance is a collection used to assign permissions for this user,
        # do not let the user move this collection.
        elif not self._user_may_move_collection(user, form.instance):
            form.fields.pop("parent")
        else:
            # Filter collections offered in parent field by current user's add permissions
            collections = self.permission_policy.instances_user_has_permission_for(
                user, "add"
            )
            form.fields["parent"].queryset = collections
            # Disable unavailable options in CollectionChoiceField select widget
            form.fields["parent"].disabled_queryset = form.instance.get_descendants(
                inclusive=True
            )

        form.initial["parent"] = form.instance.get_parent().pk
        return form

    def save_instance(self):
        instance = self.form.save()
        if "parent" in self.form.changed_data:
            instance.move(self.form.cleaned_data["parent"], "sorted-child")
        return instance

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_delete"] = (
            self.permission_policy.instances_user_has_permission_for(
                self.request.user, "delete"
            )
            .filter(pk=self.object.pk)
            .first()
        )
        return context


class Delete(DeleteView):
    permission_policy = collection_permission_policy
    model = Collection
    success_message = gettext_lazy("Collection '{0}' deleted.")
    index_url_name = "wagtailadmin_collections:index"
    delete_url_name = "wagtailadmin_collections:delete"
    page_title = gettext_lazy("Delete collection")
    confirmation_message = gettext_lazy(
        "Are you sure you want to delete this collection?"
    )
    header_icon = "folder-open-1"

    def get_queryset(self):
        return self.permission_policy.instances_user_has_permission_for(
            self.request.user, "delete"
        ).exclude(depth=1)

    def get_collection_contents(self):
        collection_contents = [
            hook(self.object)
            for hook in hooks.get_hooks("describe_collection_contents")
        ]

        # filter out any hook responses that report that the collection is empty
        # (by returning None, or a dict with 'count': 0)
        def is_nonempty(item_type):
            return item_type and item_type["count"] > 0

        return list(filter(is_nonempty, collection_contents))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection_contents = self.get_collection_contents()

        if collection_contents:
            # collection is non-empty; render the 'not allowed to delete' response
            self.template_name = "wagtailadmin/collections/delete_not_empty.html"
            context["collection_contents"] = collection_contents

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
