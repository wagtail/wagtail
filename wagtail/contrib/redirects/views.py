from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.vary import vary_on_headers

from wagtail.admin import messages
from wagtail.admin.auth import PermissionPolicyChecker, permission_denied
from wagtail.admin.forms.search import SearchForm
from wagtail.contrib.redirects import models
from wagtail.contrib.redirects.base_formats import DEFAULT_FORMATS
from wagtail.contrib.redirects.forms import ConfirmImportForm, ImportForm, RedirectForm
from wagtail.contrib.redirects.permissions import permission_policy
from wagtail.contrib.redirects.tmp_storages import TempFolderStorage
from wagtail.contrib.redirects.utils import get_import_formats, write_to_tmp_storage

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
    if request.is_ajax():
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
        return permission_denied(request)

    if request.method == 'POST':
        form = RedirectForm(request.POST, request.FILES, instance=theredirect)
        if form.is_valid():
            form.save()
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
        return permission_denied(request)

    if request.method == 'POST':
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
            theredirect = form.save()

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
    from_encoding = "utf-8"
    query_string = request.GET.get('q', "")

    if not request.POST:
        SUPPORTED_FORMATS = ["CSV", "TSV", "XLS", "XLSX"]
        accepted_formats = [
            x for x in DEFAULT_FORMATS if x.__name__ in SUPPORTED_FORMATS
        ]
        return render(
            request,
            "wagtailredirects/choose_import_file.html",
            {
                'search_form': SearchForm(
                    data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")
                ),
                "form": ImportForm(accepted_formats),
            },
        )

    form_kwargs = {}
    form = ImportForm(
        DEFAULT_FORMATS, request.POST or None, request.FILES or None, **form_kwargs
    )

    if not form.is_valid():
        return render(
            request,
            "wagtailredirects/choose_import_file.html", {
                'search_form': SearchForm(
                    data=dict(q=query_string) if query_string else None, placeholder=_("Search redirects")
                ),
                "form": form,
            }
        )

    import_formats = get_import_formats()
    input_format = import_formats[int(form.cleaned_data["input_format"])]()
    import_file = form.cleaned_data["import_file"]
    tmp_storage = write_to_tmp_storage(import_file, input_format)

    try:
        data = tmp_storage.read(input_format.get_read_mode())
        if not input_format.is_binary() and from_encoding:
            data = force_str(data, from_encoding)
        dataset = input_format.create_dataset(data)
    except UnicodeDecodeError as e:
        return HttpResponse(_(u"<h1>Imported file has a wrong encoding: %s</h1>" % e))
    except Exception as e:  # pragma: no cover
        return HttpResponse(
            _(
                u"<h1>%s encountered while trying to read file: %s</h1>"
                % (type(e).__name__, import_file.name)
            )
        )

    initial = {
        "import_file_name": tmp_storage.name,
        "original_file_name": import_file.name,
        "input_format": form.cleaned_data["input_format"],
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
    from_encoding = "utf-8"
    form_kwargs = {}
    form = ConfirmImportForm(
        DEFAULT_FORMATS, request.POST or None, request.FILES or None, **form_kwargs
    )

    is_confirm_form_valid = form.is_valid()

    import_formats = get_import_formats()
    input_format = import_formats[int(form.cleaned_data["input_format"])]()
    tmp_storage = TempFolderStorage(name=form.cleaned_data["import_file_name"])

    if not is_confirm_form_valid:
        data = tmp_storage.read(input_format.get_read_mode())
        dataset = input_format.create_dataset(data)

        initial = {
            "import_file_name": tmp_storage.name,
            "original_file_name": form.cleaned_data["import_file_name"],
            "input_format": form.cleaned_data["input_format"],
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

    data = tmp_storage.read(input_format.get_read_mode())
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

    tmp_storage.remove()

    return render(
        request,
        "wagtailredirects/import_summary.html",
        {
            "form": ImportForm(DEFAULT_FORMATS),
            "import_summary": import_summary,
        },
    )


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
            error = form.errors.as_text().replace("\n", "")
            errors.append([from_link, to_link, error])
            continue

        form.save()
        successes += 1

    return {
        "errors": errors,
        "errors_count": len(errors),
        "successes": successes,
        "total": total,
    }
