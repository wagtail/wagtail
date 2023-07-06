from django import forms
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy

from wagtail.admin import messages
from wagtail.admin.auth import user_passes_test
from wagtail.admin.views.generic import DeleteView, EditView, IndexView
from wagtail.contrib.forms.views import SubmissionsListView

from .models import ModelWithStringTypePrimaryKey


def user_is_called_bob(user):
    return user.first_name == "Bob"


@user_passes_test(user_is_called_bob)
def bob_only_zone(request):
    return HttpResponse("Bobs of the world unite!")


def message_test(request):
    if request.method == "POST":
        fn = getattr(messages, request.POST["level"])
        fn(request, request.POST["message"])
        return redirect("testapp_message_test")
    else:
        return TemplateResponse(request, "wagtailadmin/base.html")


class CustomSubmissionsListView(SubmissionsListView):
    paginate_by = 50
    ordering = ("submit_time",)
    ordering_csv = ("-submit_time",)

    def get_csv_filename(self):
        """Returns the filename for CSV file with page title at start"""
        filename = super().get_csv_filename()
        return self.form_page.slug + "-" + filename


class TestIndexView(IndexView):

    model = ModelWithStringTypePrimaryKey
    index_url_name = "testapp_generic_index"
    template_name = "tests/generic_view_templates/index.html"
    paginate_by = 20
    context_object_name = "test_object"
    page_title = gettext_lazy("test index view")


class CustomModelEditForm(forms.ModelForm):
    class Meta:
        model = ModelWithStringTypePrimaryKey
        fields = ("content",)


class TestEditView(EditView):

    model = ModelWithStringTypePrimaryKey
    context_object_name = "test_object"
    template_name = "tests/generic_view_templates/edit.html"
    index_url_name = "testapp_generic_index"
    success_url = "testapp_generic_index"
    edit_url_name = "testapp_generic_edit"
    delete_url_name = "testapp_generic_delete"
    form_class = CustomModelEditForm
    success_message = gettext_lazy("User '%(object)s' updated.")
    page_title = gettext_lazy("test edit view")


class TestDeleteView(DeleteView):

    model = ModelWithStringTypePrimaryKey
    context_object_name = "test_object"
    template_name = "tests/generic_view_templates/delete.html"
    index_url_name = "testapp_generic_index"
    edit_url_name = "testapp_generic_edit"
    delete_url_name = "testapp_generic_delete"
    success_message = gettext_lazy("User '%(object)s' updated.")
    page_title = gettext_lazy("test delete view")
