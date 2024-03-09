from django.contrib.admin.utils import quote
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import FormView

from wagtail.admin.forms.pages import ParentChooserForm
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin
from wagtail.models import Page


class ChooseParentView(WagtailAdminTemplateMixin, FormView):
    template_name = "wagtailadmin/pages/choose_parent.html"
    model = Page
    index_url_name = None
    page_title = gettext_lazy("Choose parent")

    def get_form(self):
        if self.request.method == "POST":
            return ParentChooserForm(self.model, self.request.user, self.request.POST)
        return ParentChooserForm(self.model, self.request.user)

    def get_index_url(self):
        if self.index_url_name:
            return reverse(self.index_url_name)

    def get_breadcrumbs_items(self):
        items = []
        index_url = self.get_index_url()
        if index_url:
            items.append(
                {
                    "url": index_url,
                    "label": capfirst(self.model._meta.verbose_name_plural),
                }
            )
        items.append(
            {
                "url": "",
                "label": self.get_page_title(),
                "sublabel": self.get_page_subtitle(),
            }
        )

        return self.breadcrumbs_items + items

    def get_page_subtitle(self):
        return self.model.get_verbose_name()

    @cached_property
    def submit_button_label(self):
        return _("Create a new %(model_name)s") % {
            "model_name": self.model._meta.verbose_name,
        }

    def form_valid(self, form):
        model_opts = self.model._meta
        parent_id = quote(form.cleaned_data["parent_page"].pk)
        return redirect(
            "wagtailadmin_pages:add",
            model_opts.app_label,
            model_opts.model_name,
            parent_id,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["media"] = context["form"].media
        context["submit_button_label"] = self.submit_button_label
        return context
