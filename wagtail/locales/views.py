from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.admin.views import generic
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.models import Locale
from wagtail.permissions import locale_permission_policy

from .forms import LocaleForm
from .utils import get_locale_usage


class LanguageTitleColumn(TitleColumn):
    cell_template_name = "wagtaillocales/_language_title_cell.html"

    def get_value(self, locale):
        return locale


class UsageColumn(Column):
    def get_value(self, locale):
        num_pages, num_others = get_locale_usage(locale)
        # TODO: make this translatable
        val = "%d pages" % num_pages
        if num_others:
            val += " + %d others" % num_others
        return val


class IndexView(generic.IndexView):
    page_title = gettext_lazy("Locales")
    add_item_label = gettext_lazy("Add a locale")
    context_object_name = "locales"
    queryset = Locale.all_objects.all()
    default_ordering = "language_code"

    columns = [
        LanguageTitleColumn(
            "language",
            label=gettext_lazy("Language"),
            sort_key="language_code",
            url_name="wagtaillocales:edit",
        ),
        UsageColumn("usage", label=gettext_lazy("Usage")),
    ]


class CreateView(generic.CreateView):
    page_title = gettext_lazy("Add locale")
    success_message = gettext_lazy("Locale '%(object)s' created.")


class EditView(generic.EditView):
    success_message = gettext_lazy("Locale '%(object)s' updated.")
    error_message = gettext_lazy("The locale could not be saved due to errors.")
    delete_item_label = gettext_lazy("Delete locale")
    context_object_name = "locale"
    queryset = Locale.all_objects.all()


class DeleteView(generic.DeleteView):
    success_message = gettext_lazy("Locale '%(object)s' deleted.")
    page_title = gettext_lazy("Delete locale")
    confirmation_message = gettext_lazy("Are you sure you want to delete this locale?")
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
        context = super().get_context_data()
        context["can_delete"] = self.can_delete(object)
        return context

    def form_valid(self, form):
        if self.can_delete(self.get_object()):
            return super().form_valid(form)
        else:
            messages.error(self.request, self.cannot_delete_message)
            return super().get(self.request)


class LocaleViewSet(ModelViewSet):
    icon = "site"
    model = Locale
    permission_policy = locale_permission_policy
    add_to_reference_index = False
    _show_breadcrumbs = False

    index_view_class = IndexView
    add_view_class = CreateView
    edit_view_class = EditView
    delete_view_class = DeleteView

    template_prefix = "wagtaillocales/"

    def get_common_view_kwargs(self, **kwargs):
        return super().get_common_view_kwargs(
            **{
                "history_url_name": None,
                "usage_url_name": None,
                **kwargs,
            }
        )

    def get_form_class(self, for_update=False):
        return LocaleForm
