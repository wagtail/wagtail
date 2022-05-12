import $ from 'jquery';
import { SearchController } from '../../includes/chooserModal';

window.SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  choose: function (modal) {
    function ajaxifyLinks(context) {
      $('a.snippet-choice', modal.body).on('click', function () {
        modal.loadUrl(this.href);
        return false;
      });

      $('.pagination a', context).on('click', function () {
        searchController.fetchResults(this.href);
        return false;
      });
    }

    const searchController = new SearchController({
      form: $('form.snippet-search', modal.body),
      resultsContainerSelector: '#search-results',
      onLoadResults: (context) => {
        ajaxifyLinks(context);
      },
    });
    searchController.attachSearchInput('#id_q');
    searchController.attachSearchFilter('#snippet-chooser-locale');

    ajaxifyLinks(modal.body);
  },
  chosen: function (modal, jsonData) {
    modal.respond('snippetChosen', jsonData.result);
    modal.close();
  },
};
