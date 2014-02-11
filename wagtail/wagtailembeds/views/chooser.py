from django.forms.util import ErrorList
from django.conf import settings

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailembeds.forms import EmbedForm
from wagtail.wagtailembeds.format import embed_to_editor_html


def chooser(request):
    form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })


def chooser_upload(request):
    if request.POST:
        form = EmbedForm(request.POST, request.FILES)

        if form.is_valid():
            embed_html = embed_to_editor_html(form.cleaned_data['url'])
            if embed_html != "":
                return render_modal_workflow(
                    request, None, 'wagtailembeds/chooser/embed_chosen.js',
                    {'embed_html': embed_html}
                )
            else:
                errors = form._errors.setdefault('url', ErrorList())
                if not hasattr(settings, 'EMBEDLY_KEY'):
                    errors.append('Please set EMBEDLY_KEY in your settings')
                else:
                    errors.append('This URL is not recognised')
                return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
                    'form': form,
                })
    else:
        form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })
