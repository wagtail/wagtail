from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views.generic import TemplateView
from django.views.generic.detail import SingleObjectMixin
from wagtail.admin.views.pages.utils import get_valid_next_url_from_request
from wagtail.contrib.simple_translation.forms import SubmitTranslationForm
from wagtail.core.models import Locale, Page, TranslatableMixin
from wagtail.snippets.views.snippets import get_snippet_model_from_url_params


class SubmitTranslationView(SingleObjectMixin, TemplateView):
    template_name = "simple_translation/admin/submit_translation.html"
    title = gettext_lazy("Translate")

    def get_title(self):
        return self.title

    def get_subtitle(self):
        return str(self.object)

    def get_form(self):
        if self.request.method == "POST":
            return SubmitTranslationForm(self.object, self.request.POST)
        else:
            return SubmitTranslationForm(self.object)

    def get_success_url(self):
        return get_valid_next_url_from_request(self.request)

    def get_default_success_url(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "form": self.get_form(),
                "next_url": self.get_success_url(),
                "back_url": self.get_success_url() or self.get_default_success_url(),
            }
        )
        return context

    def post(self, request, **kwargs):
        form = self.get_form()

        if form.is_valid():
            with transaction.atomic():
                for locale in form.cleaned_data["locales"]:
                    if isinstance(self.object, Page):
                        self.object.copy_for_translation(locale)
                        if form.cleaned_data["include_subtree"]:

                            def _walk(current_page):
                                for child_page in current_page.get_children():
                                    child_page.copy_for_translation(locale)

                                    if child_page.numchild:
                                        _walk(child_page)

                            _walk(self.object)
                    else:
                        self.object.copy_for_translation(locale).save()

                if len(form.cleaned_data["locales"]) == 1:
                    locales = form.cleaned_data["locales"][0].get_display_name()

                else:
                    # Note: always plural
                    locales = _("{} locales").format(len(form.cleaned_data["locales"]))

                messages.success(self.request, self.get_success_message(locales))

                return redirect(
                    self.get_success_url() or self.get_default_success_url()
                )

        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perms(["simple_translation.submit_translation"]):
            raise PermissionDenied

        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)


class SubmitPageTranslationView(SubmitTranslationView):
    title = gettext_lazy("Translate page")

    def get_subtitle(self):
        return self.object.get_admin_display_title()

    def get_object(self):
        page = get_object_or_404(Page, id=self.kwargs["page_id"]).specific

        # Can't translate the root page
        if page.is_root():
            raise Http404

        return page

    def get_default_success_url(self):
        return reverse("wagtailadmin_explore", args=[self.get_object().get_parent().id])

    def get_success_message(self, locales):
        return _("The page '{page_title}' was successfully created {locales}").format(
            page_title=self.object.get_admin_display_title(), locales=locales
        )


class SubmitSnippetTranslationView(SubmitTranslationView):
    def get_title(self):
        return _("Translate {model_name}").format(
            model_name=self.object._meta.verbose_name
        )

    def get_object(self):
        model = get_snippet_model_from_url_params(
            self.kwargs["app_label"], self.kwargs["model_name"]
        )

        if not issubclass(model, TranslatableMixin):
            raise Http404

        return get_object_or_404(model, pk=unquote(self.kwargs["pk"]))

    def get_default_success_url(self):
        return reverse(
            "wagtailsnippets:edit",
            args=[
                self.kwargs["app_label"],
                self.kwargs["model_name"],
                self.kwargs["pk"],
            ],
        )

    def get_success_message(self, locales):
        return _(
            "The {model_name} '{object}' was successfully submitted for translation into {locales}"
        ).format(
            model_name=self.object._meta.verbose_name,
            object=str(self.object),
            locales=locales,
        )
