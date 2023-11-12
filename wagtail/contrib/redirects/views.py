import os

from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy, ngettext
from django.views.decorators.http import require_http_methods

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.views.generic import CreateView, DeleteView, EditView, IndexView
from wagtail.admin.views.reports import ReportView
from wagtail.contrib.redirects import models
from wagtail.contrib.redirects.filters import RedirectsReportFilterSet
from wagtail.contrib.redirects.forms import (
    ConfirmImportForm,
    ConfirmImportManagementForm,
    ImportForm,
    RedirectForm,
)
from wagtail.contrib.redirects.models import Redirect
from wagtail.contrib.redirects.permissions import permission_policy
from wagtail.contrib.redirects.utils import (
    get_file_storage,
    get_format_cls_by_extension,
    get_import_formats,
    get_supported_extensions,
    write_to_file_storage,
)
from wagtail.log_actions import log

permission_checker = PermissionPolicyChecker(permission_policy)


class Index(IndexView):
    """
    Lists all redirects for management within the admin.
    """

    template_name = "wagtailredirects/index.html"
    results_template_name = "wagtailredirects/results.html"
    any_permission_required = ["add", "change", "delete"]
    permission_policy = permission_policy
    model = Redirect
    header_icon = "redirects"
    add_item_label = _("Add redirect")
    context_object_name = "redirects"
    index_url_name = "wagtailredirects:index"
    add_url_name = "wagtailredirects:add"
    edit_url_name = "wagtailredirects:edit"
    delete_url_name = "wagtailredirects:delete"
    default_ordering = "old_path"
    paginate_by = 20
    is_searchable = True
    page_title = gettext_lazy("Redirects")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.redirects = Redirect.objects.prefetch_related("redirect_page", "site")
        self.query_string = request.GET.get("q", "")

    def get_index_results_url(self):
        if self.query_string:
            return reverse("wagtailredirects:index_results")
        else:
            return reverse("wagtailredirects:index")

    def get_valid_orderings(self):
        return ["old_path"]

    def get_queryset(self):
        redirects = self.redirects
        if self.is_searching:
            if self.query_string:
                redirects = redirects.filter(
                    Q(old_path__icontains=self.query_string)
                    | Q(redirect_page__url_path__icontains=self.query_string)
                    | Q(redirect_link__icontains=self.query_string)
                )

        if self.get_ordering() == "old_path":
            redirects = redirects.order_by(self.default_ordering)

        return redirects

    def get_context_data(self, *args, object_list=None, **kwargs):
        context_data = super().get_context_data(
            *args, object_list=object_list, **kwargs
        )

        context_data["ordering"] = self.default_ordering
        context_data["redirects"] = self.get_queryset()
        return context_data


class Edit(EditView):
    """
    Provide the ability to edit a redirect within the admin
    """

    model = Redirect
    permission_policy = permission_policy
    form_class = RedirectForm
    header_icon = "redirects"
    index_url_name = "wagtailredirects:index"
    edit_url_name = "wagtailredirects:edit"
    delete_url_name = "wagtailredirects:delete"
    success_message = gettext_lazy("Redirect '%(object)s' updated.")
    context_object_name = "redirects"
    error_message = gettext_lazy("The redirect could not be saved due to errors.")

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.object = self.get_object()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect"] = self.object
        return context


class Delete(DeleteView):
    """
    Provide the ability to delete a redirect within the admin
    """

    permission_policy = permission_policy
    model = Redirect
    index_url_name = "wagtailredirects:index"
    edit_url_name = "wagtailredirects:edit"
    delete_url_name = "wagtailredirects:delete"
    page_title = gettext_lazy("Delete Redirect")
    context_object_name = "redirect"
    success_message = gettext_lazy("Redirect '%(object)s' deleted.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect"] = self.object
        return context


class Create(CreateView):
    """
    Provide the ability to create a redirect within the admin
    """

    permission_policy = permission_policy
    permission_required = "add"
    model = Redirect
    form_class = RedirectForm
    template_name = "wagtailredirects/add.html"
    add_url_name = "wagtailredirects:add"
    index_url_name = "wagtailredirects:index"
    edit_url_name = "wagtailredirects:edit"
    delete_url_name = "wagtailredirects:delete"
    header_icon = "redirect"
    page_title = gettext_lazy("Add redirect")
    success_message = gettext_lazy("Redirect '%(object)s' created.")
    error_message = gettext_lazy("The redirect could not be created due to errors.")


@permission_checker.require_any("add")
def start_import(request):
    supported_extensions = get_supported_extensions()
    from_encoding = "utf-8"

    query_string = request.GET.get("q", "")

    if request.POST or request.FILES:
        form_kwargs = {}
        form = ImportForm(
            supported_extensions,
            request.POST or None,
            request.FILES or None,
            **form_kwargs,
        )
    else:
        form = ImportForm(supported_extensions)

    if not request.FILES or not form.is_valid():
        return render(
            request,
            "wagtailredirects/choose_import_file.html",
            {
                "search_form": SearchForm(
                    data={"q": query_string} if query_string else None,
                    placeholder=_("Search redirects"),
                ),
                "form": form,
            },
        )

    import_file = form.cleaned_data["import_file"]

    _name, extension = os.path.splitext(import_file.name)
    extension = extension.lstrip(".")

    if extension not in supported_extensions:
        messages.error(
            request,
            _('File format of type "%(extension)s" is not supported')
            % {"extension": extension},
        )
        return redirect("wagtailredirects:start_import")

    import_format_cls = get_format_cls_by_extension(extension)
    input_format = import_format_cls()
    file_storage = write_to_file_storage(import_file, input_format)

    try:
        data = file_storage.read(input_format.get_read_mode())
        if not input_format.is_binary() and from_encoding:
            data = force_str(data, from_encoding)
        dataset = input_format.create_dataset(data)
    except UnicodeDecodeError as e:
        messages.error(
            request,
            _("Imported file has a wrong encoding: %(error_message)s")
            % {"error_message": e},
        )
        return redirect("wagtailredirects:start_import")
    except Exception as e:  # noqa: BLE001; pragma: no cover
        messages.error(
            request,
            _("%(error)s encountered while trying to read file: %(filename)s")
            % {"error": type(e).__name__, "filename": import_file.name},
        )
        return redirect("wagtailredirects:start_import")

    # This data is needed in the processing step, so it is stored in
    # hidden form fields as signed strings (signing happens in the form).
    initial = {
        "import_file_name": os.path.basename(file_storage.name),
        "input_format": get_import_formats().index(import_format_cls),
    }

    return render(
        request,
        "wagtailredirects/confirm_import.html",
        {
            "form": ConfirmImportForm(dataset.headers, initial=initial),
            "dataset": dataset,
        },
    )


@permission_checker.require_any("add")
@require_http_methods(["POST"])
def process_import(request):
    supported_extensions = get_supported_extensions()
    from_encoding = "utf-8"

    management_form = ConfirmImportManagementForm(request.POST)
    if not management_form.is_valid():
        # Unable to unsign the hidden form data, or the data is missing, that's suspicious.
        raise SuspiciousOperation(
            f"Invalid management form, data is missing or has been tampered with:\n"
            f"{management_form.errors.as_text()}"
        )

    input_format = get_import_formats()[
        int(management_form.cleaned_data["input_format"])
    ]()

    FileStorage = get_file_storage()
    file_storage = FileStorage(name=management_form.cleaned_data["import_file_name"])

    data = file_storage.read(input_format.get_read_mode())
    if not input_format.is_binary() and from_encoding:
        data = force_str(data, from_encoding)
    dataset = input_format.create_dataset(data)

    # Now check if the rest of the management form is valid
    form = ConfirmImportForm(
        dataset.headers,
        request.POST,
        request.FILES,
        initial=management_form.cleaned_data,
    )

    if not form.is_valid():
        return render(
            request,
            "wagtailredirects/confirm_import.html",
            {
                "form": form,
                "dataset": dataset,
            },
        )

    import_summary = create_redirects_from_dataset(
        dataset,
        {
            "from_index": int(form.cleaned_data["from_index"]),
            "to_index": int(form.cleaned_data["to_index"]),
            "permanent": form.cleaned_data["permanent"],
            "site": form.cleaned_data["site"],
        },
    )

    file_storage.remove()

    if import_summary["errors_count"] > 0:
        return render(
            request,
            "wagtailredirects/import_summary.html",
            {
                "form": ImportForm(supported_extensions),
                "import_summary": import_summary,
            },
        )

    total = import_summary["total"]
    messages.success(
        request,
        ngettext("Imported %(total)d redirect", "Imported %(total)d redirects", total)
        % {"total": total},
    )

    return redirect("wagtailredirects:index")


def create_redirects_from_dataset(dataset, config):
    errors = []
    successes = 0
    total = 0

    for row in dataset:
        total += 1

        from_link = row[config["from_index"]]
        to_link = row[config["to_index"]]

        data = {
            "old_path": from_link,
            "redirect_link": to_link,
            "is_permanent": config["permanent"],
        }

        if config["site"]:
            data["site"] = config["site"].pk

        form = RedirectForm(data)
        if not form.is_valid():
            error = to_readable_errors(form.errors.as_text())
            errors.append([from_link, to_link, error])
            continue

        with transaction.atomic():
            redirect = form.save()
            log(instance=redirect, action="wagtail.create")
        successes += 1

    return {
        "errors": errors,
        "errors_count": len(errors),
        "successes": successes,
        "total": total,
    }


def to_readable_errors(error):
    errors = error.split("\n")
    errors = errors[1::2]
    errors = [x.lstrip("* ") for x in errors]
    errors = ", ".join(errors)
    return errors


class RedirectsReportView(ReportView):
    header_icon = "redirect"
    title = _("Export Redirects")
    template_name = "wagtailredirects/reports/redirects_report.html"
    filterset_class = RedirectsReportFilterSet

    list_export = [
        "old_path",
        "link",
        "get_is_permanent_display",
        "site",
    ]

    export_headings = {
        "old_path": _("From"),
        "site": _("Site"),
        "link": _("To"),
        "get_is_permanent_display": _("Type"),
    }

    def get_queryset(self):
        return models.Redirect.objects.all().order_by("old_path")
