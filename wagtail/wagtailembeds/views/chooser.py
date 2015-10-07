import json

from django.forms.utils import ErrorList
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


from wagtail.wagtailadmin.modal_workflow import render_modal_workflow
from wagtail.wagtailadmin.forms import SearchForm
from wagtail.wagtailembeds.forms import EmbedForm
from wagtail.wagtailembeds.format import embed_to_editor_html
from wagtail.wagtailembeds import embeds

from wagtail.wagtailembeds.embeds import EmbedNotFoundException, EmbedlyException, AccessDeniedEmbedlyException
from wagtail.wagtailembeds.models import Embed

from wagtail.wagtailembeds.embeds import oembed


def get_embed_json(embed):
    """
    helper function: given an embed, return the json to pass back to the
    chooser panel
    """
    return json.dumps({
        'id': embed.id,
        'url': embed.url,
        'type': embed.type,
        'title': embed.title,
        'thumbnail_url': embed.thumbnail_url,
    })


def chooser(request):

    if request.user.has_perm('wagtailembeds.add_embed'):
        uploadform = EmbedForm()
    else:
        uploadform = None

    q = None
    if 'q' in request.GET or 'p' in request.GET:
        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            # page number
            p = request.GET.get("p", 1)

            embeds = Embed.search(q, results_per_page=10, page=p)

            is_searching = True

        else:
            embeds = Embed.objects.order_by('-last_updated')
            p = request.GET.get("p", 1)
            paginator = Paginator(embeds, 10)

            try:
                embeds = paginator.page(p)
            except PageNotAnInteger:
                embeds = paginator.page(1)
            except EmptyPage:
                embeds = paginator.page(paginator.num_pages)

            is_searching = False

        return render(request, "wagtailembeds/chooser/results.html", {
            'embeds': embeds,
            'is_searching': is_searching,
            'query_string': q
        })
    else:
        searchform = SearchForm()

        embeds = Embed.objects.order_by('-last_updated')
        p = request.GET.get("p", 1)
        paginator = Paginator(embeds, 10)

        try:
            embeds = paginator.page(p)
        except PageNotAnInteger:
            embeds = paginator.page(1)
        except EmptyPage:
            embeds = paginator.page(paginator.num_pages)

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'embeds': embeds,
        'form': uploadform,
        'searchform': searchform,
        'is_searching': False,
        'query_string': q,

    })


def chooser_upload(request):
    if request.POST:
        form = EmbedForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                embed = embeds.get_embed(form.cleaned_data['url'])
                embed_html = embed_to_editor_html(embed.url)
                embed_json = get_embed_json(embed)
                return render_modal_workflow(
                    request, None, 'wagtailembeds/chooser/embed_chosen.js',
                    {
                        'embed_html': embed_html,
                        'embed_json': embed_json,
                    }
                )
            except AccessDeniedEmbedlyException:
                error = _("There seems to be a problem with your embedly API key. Please check your settings.")
            except EmbedNotFoundException:
                error = _("Cannot find an embed for this URL.")
            except EmbedlyException:
                error = _("There seems to be an error with Embedly while trying to embed this URL. Please try again later.")

            if error:
                errors = form._errors.setdefault('url', ErrorList())
                errors.append(error)
                return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
                    'form': form,
                })
    else:
        form = EmbedForm()

    return render_modal_workflow(request, 'wagtailembeds/chooser/chooser.html', 'wagtailembeds/chooser/chooser.js', {
        'form': form,
    })


def embed_chosen(request, embed_id):
    embed = get_object_or_404(Embed, id=embed_id)
    embed_html = embed_to_editor_html(embed.url)
    embed_json = get_embed_json(embed)
    return render_modal_workflow(
        request, None, 'wagtailembeds/chooser/embed_chosen.js',
        {
            'embed_html': embed_html,
            'embed_json': embed_json,
        }
    )
