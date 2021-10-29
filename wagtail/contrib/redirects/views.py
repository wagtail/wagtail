import os

from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker
from wagtail.admin.forms.search import SearchForm
from wagtail.admin.views.reports import ReportView
from wagtail.contrib.redirects import models
from wagtail.contrib.redirects.base_formats import DEFAULT_FORMATS
from wagtail.contrib.redirects.filters import RedirectsReportFilterSet
from wagtail.contrib.redirects.forms import ConfirmImportForm, ImportForm, RedirectForm
from wagtail.contrib.redirects.permissions import permission_policy
from wagtail.contrib.redirects.utils import (
    get_file_storage, get_format_cls_by_extension, get_import_formats, get_supported_extensions,
    write_to_file_storage)
from wagtail.core.log_actions import log


permission_checker = PermissionPolicyChecker(permission_policy)


@permission_checker.require_any('add', 'change', 'delete')
@vary_on_headers('X-Requested-With')
def index(request):
    query_string = request.GET.get('q', "")
    ordering = request.GET.get('ordering', 'old_path')

    redirects = models.Redirect.objects.prefetch_related('redirect_page', 'site')

    # Search
    if query_string:
        redirects = redirects.filter(Q(old_path__icontains=query_string)
                                     | Q(redirect_page__url_path__icontains=query_string)
                                     | Q(redirect_link__icontains=query_string))

    # Ordering (A bit useless at the moment as only 'old_path' is allowed)
    if ordering not in ['old_path']:
        ordering = 'old_path'

    redirects = redirects.order_by(ordering)

    # Pagination
    paginator = Paginator(redirects, per_page=20)
    redirects = paginator.get_page(request.GET.get('p'))

    # Render template
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return TemplateResponse(request, "wagtailredirects/results.html", {
            'ordering': ordering,
            'redirects': redirects,
            'query_string': query_string,
        })
    else:
        return TemplateResponse(request, "wagtailredirects/index.html", {
            'ordering': ordering,
            'redirects': redirects,
            'query_string': query_string,
            'search_form': SearchForm(
                data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")
            ),
            'user_can_add': permission_policy.user_has_permission(request.user, 'add'),
        })


@permission_checker.require('change')
def edit(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, 'change', theredirect
    ):
        raise PermissionDenied

    if request.method == 'POST':
        form = RedirectForm(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                log(instance=theredirect, action='wagtail.edit')
            messages.success(request, _("Redirect '{0}' updated.").format(theredirect.title), buttons=[
                messages.button(reverse('wagtailredirects:edit', args=(theredirect.id,)), _('Edit'))
            ])
            return redirect('wagtailredirects:index')
        else:
            messages.error(request, _("The redirect could not be saved due to errors."))
    else:
        form = RedirectForm(instance=theredirect)

    return TemplateResponse(request, "wagtailredirects/edit.html", {
        'redirect': theredirect,
        'form': form,
        'user_can_delete': permission_policy.user_has_permission(request.user, 'delete'),
    })


@permission_checker.require('delete')
def delete(request, redirect_id):
    theredirect = get_object_or_404(models.Redirect, id=redirect_id)

    if not permission_policy.user_has_permission_for_instance(
        request.user, 'delete', theredirect
    ):
        raise PermissionDenied

    if request.method == 'POST':
        with transaction.atomic():
            log(instance=theredirect, action='wagtail.delete')
            theredirect.delete()
        messages.success(request, _("Redirect '{0}' deleted.").format(theredirect.title))
        return redirect('wagtailredirects:index')

    return TemplateResponse(request, "wagtailredirects/confirm_delete.html", {
        'redirect': theredirect,
    })


@permission_checker.require('add')
def add(request):
    if request.method == 'POST':
        form = RedirectForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                theredirect = form.save()
                log(instance=theredirect, action='wagtail.edit')

            messages.success(request, _("Redirect '{0}' added.").format(theredirect.title), buttons=[
                messages.button(reverse('wagtailredirects:edit', args=(theredirect.id,)), _('Edit'))
            ])
            return redirect('wagtailredirects:index')
        else:
            messages.error(request, _("The redirect could not be created due to errors."))
    else:
        form = RedirectForm()

    return TemplateResponse(request, "wagtailredirects/add.html", {
        'form': form,
    })


@permission_checker.require_any("add")
def start_import(request):
    supported_extensions = get_supported_extensions()
    from_encoding = "utf-8"

    query_string = request.GET.get('q', "")

    if request.POST or request.FILES:
        form_kwargs = {}
        form = ImportForm(
            supported_extensions,
            request.POST or None,
            request.FILES or None,
            **form_kwargs
        )
    else:
        form = ImportForm(supported_extensions)

    if not request.FILES or not form.is_valid():
        return render(
            request,
            "wagtailredirects/choose_import_file.html",
            {
                'search_form': SearchForm(
                    data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")
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
            _('File format of type "{}" is not supported').format(extension)
        )
        return redirect('wagtailredirects:start_import')

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
            _("Imported file has a wrong encoding: %s") % e
        )
        return redirect('wagtailredirects:start_import')
    except Exception as e:  # pragma: no cover
        messages.error(
            request,
            _("%(error)s encountered while trying to read file: %(filename)s") % {
                'error': type(e).__name__, 'filename': import_file.name
            }
        )
        return redirect('wagtailredirects:start_import')

    initial = {
        "import_file_name": file_storage.name,
        "original_file_name": import_file.name,
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

    form_kwargs = {}
    form = ConfirmImportForm(
        DEFAULT_FORMATS, request.POST or None, request.FILES or None, **form_kwargs
    )

    is_confirm_form_valid = form.is_valid()

    import_formats = get_import_formats()
    input_format = import_formats[int(form.cleaned_data["input_format"])]()

    FileStorage = get_file_storage()
    file_storage = FileStorage(name=form.cleaned_data["import_file_name"])

    if not is_confirm_form_valid:
        data = file_storage.read(input_format.get_read_mode())
        if not input_format.is_binary() and from_encoding:
            data = force_str(data, from_encoding)
        dataset = input_format.create_dataset(data)

        initial = {
            "import_file_name": file_storage.name,
            "original_file_name": form.cleaned_data["import_file_name"],
        }

        return render(
            request,
            "wagtailredirects/confirm_import.html",
            {
                "form": ConfirmImportForm(
                    dataset.headers,
                    request.POST or None,
                    request.FILES or None,
                    initial=initial,
                ),
                "dataset": dataset,
            },
        )

    data = file_storage.read(input_format.get_read_mode())
    if not input_format.is_binary() and from_encoding:
        data = force_str(data, from_encoding)
    dataset = input_format.create_dataset(data)

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
        ngettext(
            "Imported %(total)d redirect",
            "Imported %(total)d redirects",
            total
        ) % {'total': total}
    )

    return redirect('wagtailredirects:index')


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
            log(instance=redirect, action='wagtail.create')
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
    errors = [x.lstrip('* ') for x in errors]
    errors = ", ".join(errors)
    return errors


class RedirectsReportView(ReportView):
    header_icon = "redirect"
    title = _("Export Redirects")
    template_name = "wagtailredirects/reports/redirects_report.html"
    filterset_class = RedirectsReportFilterSet

    list_export = [
        "old_path",
        "site",
        "link",
        "get_is_permanent_display",
    ]

    export_headings = {
        "old_path": _("From"),
        "site": _("Site"),
        "link": _("To"),
        "get_is_permanent_display": _("Type"),
    }

    def get_queryset(self):
        return models.Redirect.objects.all().order_by("old_path")
