from django.utils.translation import ugettext_lazy as __

from wagtail.wagtailcore.models import Collection
from wagtail.wagtailadmin.forms import CollectionForm
from wagtail.wagtailadmin.views.generic import IndexView, CreateView, EditView, DeleteView


class Index(IndexView):
    any_permission_required = ['wagtailcore.add_collection', 'wagtailcore.change_collection', 'wagtailcore.delete_collection']
    model = Collection
    context_object_name = 'collections'
    template_name = 'wagtailadmin/collections/index.html'
    add_url_name = 'wagtailadmin_collections:add'
    add_permission_name = 'wagtailcore.add_collection'
    page_title = __("Collections")
    add_item_label = __("Add a collection")
    header_icon = 'folder-open-1'

    def get_queryset(self):
        # Only return children of the root node, so that the root is not editable
        return Collection.get_first_root_node().get_children()


class Create(CreateView):
    permission_required = 'wagtailcore.add_collection'
    form_class = CollectionForm
    page_title = __("Add collection")
    success_message = __("Collection '{0}' created.")
    add_url_name = 'wagtailadmin_collections:add'
    edit_url_name = 'wagtailadmin_collections:edit'
    index_url_name = 'wagtailadmin_collections:index'
    header_icon = 'folder-open-1'

    def save_instance(self, form):
        instance = form.save(commit=False)
        root_collection = Collection.get_first_root_node()
        root_collection.add_child(instance=instance)
        return instance


class Edit(EditView):
    permission_required = 'wagtailcore.change_collection'
    model = Collection
    form_class = CollectionForm
    success_message = __("Collection '{0}' updated.")
    error_message = __("The collection could not be saved due to errors.")
    delete_item_label = __("Delete collection")
    edit_url_name = 'wagtailadmin_collections:edit'
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    delete_permission_name = 'wagtailcore.delete_collection'
    context_object_name = 'collection'
    header_icon = 'folder-open-1'

    def get_queryset(self):
        # Only return children of the root node, so that the root is not editable
        return Collection.get_first_root_node().get_children()


class Delete(DeleteView):
    permission_required = 'wagtailcore.delete_collection'
    model = Collection
    success_message = __("Collection '{0}' deleted.")
    index_url_name = 'wagtailadmin_collections:index'
    delete_url_name = 'wagtailadmin_collections:delete'
    page_title = __("Delete collection")
    confirmation_message = __("Are you sure you want to delete this collection?")
    header_icon = 'folder-open-1'

    def get_queryset(self):
        # Only return children of the root node, so that the root is not editable
        return Collection.get_first_root_node().get_children()
