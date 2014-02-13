from django.forms.util import ErrorList
from django.conf import settings

from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailembeds.forms import EmbedForm
from wagtail.wagtailembeds.format import embed_to_editor_html

from wagtail.wagtailembeds.embeds.oembed_api import NotImplementedOembedException
from wagtail.wagtailembeds.embeds.embed import EmbedlyException, AccessDeniedEmbedlyException, NotFoundEmbedlyException



def chooser(request):
    form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })


def chooser_upload(request):
    if request.POST:
        form = EmbedForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                embed_html = embed_to_editor_html(form.cleaned_data['url'])
                return render_modal_workflow(
                    request, None, 'wagtailembeds/chooser/embed_chosen.js',
                    {'embed_html': embed_html}
                )
            except Exception as e :
                #print e
                #import traceback
                #traceback.print_exc()
                errors = form._errors.setdefault('url', ErrorList())
                if type(e) == NotImplementedOembedException:
                    errors.append("This URL is not supported by an oembed provider. You may try embedding it using Embedly by setting a propery EMBEDLY_KEY in your settings.")
                elif type(e) == AccessDeniedEmbedlyException:
                    errors.append("There seems to be a problem with your embedly API key. Please check your settings.")
                elif type(e) == NotFoundEmbedlyException:
                    errors.append("The URL you are trying to embed cannot be found.")
                elif type(e) == EmbedlyException:
                    errors.append("There seems to be an error with Embedly while trying to embed this URL. Please try again later.")
                else:
                    errors.append(str(e)  )
                return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
                    'form': form,
                })
    else:
        form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })
