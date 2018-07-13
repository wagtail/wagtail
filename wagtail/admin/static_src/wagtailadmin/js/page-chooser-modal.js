PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS = {
    'browse': function(modal, jsonData) {
        /* Set up link-types links to open in the modal */
        $('.link-types a', modal.body).on('click', function() {
            modal.loadUrl(this.href);
            return false;
        });

        /*
        Set up submissions of the search form to open in the modal.

        FIXME: wagtailadmin.views.chooser.browse doesn't actually return a modal-workflow
        response for search queries, so this just fails with a JS error.
        Luckily, the search-as-you-type logic below means that we never actually need to
        submit the form to get search results, so this has the desired effect of preventing
        plain vanilla form submissions from completing (which would clobber the entire
        calling page, not just the modal). It would be nice to do that without throwing
        a JS error, that's all...
        */
        modal.ajaxifyForm($('form.search-form', modal.body));

        /* Set up search-as-you-type behaviour on the search box */
        var searchUrl = $('form.search-form', modal.body).attr('action');

        /* save initial page browser HTML, so that we can restore it if the search box gets cleared */
        var initialPageResultsHtml = $('.page-results', modal.body).html();

        function search() {
            var query = $('#id_q', modal.body).val();
            if (query != '') {
                $.ajax({
                    url: searchUrl,
                    data: {
                        q: query,
                        results_only: true
                    },
                    success: function(data, status) {
                        $('.page-results', modal.body).html(data);
                        ajaxifySearchResults();
                    }
                });
            } else {
                /* search box is empty - restore original page browser HTML */
                $('.page-results', modal.body).html(initialPageResultsHtml);
                ajaxifyBrowseResults();
            }
            return false;
        }

        $('#id_q', modal.body).on('input', function() {
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(search, 200);
            $(this).data('timer', wait);
        });

        /* Set up behaviour of choose-page links in the newly-loaded search results,
        to pass control back to the calling page */
        function ajaxifySearchResults() {
            $('.page-results a.choose-page', modal.body).on('click', function() {
                var pageData = $(this).data();
                modal.respond('pageChosen', $(this).data());
                modal.close();

                return false;
            });
            /* pagination links within search results should be AJAX-fetched
            and the result loaded into .page-results (and ajaxified) */
            $('.page-results a.navigate-pages', modal.body).on('click', function() {
                $('.page-results', modal.body).load(this.href, ajaxifySearchResults);
                return false;
            });
        }

        function ajaxifyBrowseResults() {
            /* Set up page navigation links to open in the modal */
            $('.page-results a.navigate-pages', modal.body).on('click', function() {
                modal.loadUrl(this.href);
                return false;
            });

            /* Set up behaviour of choose-page links, to pass control back to the calling page */
            $('a.choose-page', modal.body).on('click', function() {
                var pageData = $(this).data();
                pageData.parentId = jsonData['parent_page_id'];
                modal.respond('pageChosen', $(this).data());
                modal.close();

                return false;
            });
        }
        ajaxifyBrowseResults();

        /*
        Focus on the search box when opening the modal.
        FIXME: this doesn't seem to have any effect (at least on Chrome)
        */
        $('#id_q', modal.body).trigger('focus');
    },
    'email_link': function(modal, jsonData) {
        $('p.link-types a', modal.body).on('click', function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('form', modal.body).on('submit', function() {
            modal.postForm(this.action, $(this).serialize());
            return false;
        });
    },
    'external_link': function(modal, jsonData) {
        $('p.link-types a', modal.body).on('click', function() {
            modal.loadUrl(this.href);
            return false;
        });

        $('form', modal.body).on('submit', function() {
            modal.postForm(this.action, $(this).serialize());
            return false;
        });
    },
    'external_link_chosen': function(modal, jsonData) {
        modal.respond('pageChosen', jsonData['result']);
        modal.close();
    }
};
