from django.forms.utils import ErrorList
from django.utils.translation import ugettext as _

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailembeds.forms import EmbedForm
from wagtail.wagtailembeds.format import embed_to_editor_html

from wagtail.wagtailembeds.exceptions import EmbedNotFoundException
from wagtail.wagtailembeds.finders.embedly import EmbedlyException, AccessDeniedEmbedlyException


def chooser(request):
    form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })


def chooser_upload(request):
    if request.POST:
        form = EmbedForm(request.POST, request.FILES)

        if form.is_valid():
            error = None
            try:
                embed_html = embed_to_editor_html(form.cleaned_data['url'])
                return render_modal_workflow(
                    request, None, 'wagtailembeds/chooser/embed_chosen.js',
                    {'embed_html': embed_html}
                )
            except AccessDeniedEmbedlyException:
                error = _("There seems to be a problem with your embedly API key. Please check your settings.")
            except EmbedNotFoundException:
                error = _("Cannot find an embed for this URL.")
            except EmbedlyException:
                error = _(
                    "There seems to be an error with Embedly while trying to embed this URL."
                    " Please try again later."
                )

            if error:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append(error)
                return render_modal_workflow(
                    request,
                    'wagtailembeds/chooser/chooser.html',
                    'wagtailembeds/chooser/chooser.js',
                    {
                        'form': form,
                    }
                )
    else:
        form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })
