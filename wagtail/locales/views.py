from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.core.models import Locale
from wagtail.core.permissions import locale_permission_policy

from .forms import LocaleForm
from .utils import get_locale_usage


class IndexView(generic.IndexView):
    template_name = 'wagtaillocales/index.html'
    page_title = gettext_lazy("Locales")
    add_item_label = gettext_lazy("Add a locale")
    context_object_name = 'locales'
    queryset = Locale.all_objects.all()

    def get_context_data(self):
        context = super().get_context_data()

        for locale in context['locales']:
            locale.num_pages, locale.num_others = get_locale_usage(locale)

        return context


class CreateView(generic.CreateView):
    page_title = gettext_lazy("Add locale")
    success_message = gettext_lazy("Locale '{0}' created.")
    template_name = 'wagtaillocales/create.html'


class EditView(generic.EditView):
    success_message = gettext_lazy("Locale '{0}' updated.")
    error_message = gettext_lazy("The locale could not be saved due to errors.")
    delete_item_label = gettext_lazy("Delete locale")
    context_object_name = 'locale'
    template_name = 'wagtaillocales/edit.html'
    queryset = Locale.all_objects.all()


class DeleteView(generic.DeleteView):
    success_message = gettext_lazy("Locale '{0}' deleted.")
    page_title = gettext_lazy("Delete locale")
    confirmation_message = gettext_lazy("Are you sure you want to delete this locale?")
    template_name = 'wagtaillocales/confirm_delete.html'
    queryset = Locale.all_objects.all()

    def can_delete(self, locale):
        if not self.queryset.exclude(pk=locale.pk).exists():
            self.cannot_delete_message = gettext_lazy(
                "This locale cannot be deleted because there are no other locales."
            )
            return False

        if get_locale_usage(locale) != (0, 0):
            self.cannot_delete_message = gettext_lazy(
                "This locale cannot be deleted because there are pages and/or other objects using it."
            )
            return False

        return True

    def get_context_data(self, object=None):
        context = context = super().get_context_data()
        context['can_delete'] = self.can_delete(object)
        return context

    def delete(self, request, *args, **kwargs):
        if self.can_delete(self.get_object()):
            return super().delete(request, *args, **kwargs)
        else:
            messages.error(request, self.cannot_delete_message)
            return super().get(request)


class LocaleViewSet(ModelViewSet):
    icon = 'site'
    model = Locale
    permission_policy = locale_permission_policy

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    def get_form_class(self, for_update=False):
        return LocaleForm
