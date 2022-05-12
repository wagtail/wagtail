import $ from 'jquery';
import { SearchController } from '../../includes/chooserModal';

window.SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  choose: (modal) => {
    let searchController;

    function ajaxifyLinks(context) {
      $('a.snippet-choice', modal.body).on('click', (event) => {
        modal.loadUrl(event.currentTarget.href);
        return false;
      });

      $('.pagination a', context).on('click', (event) => {
        searchController.fetchResults(event.currentTarget.href);
        return false;
      });
    }

    searchController = new SearchController({
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
  chosen: (modal, jsonData) => {
    modal.respond('snippetChosen', jsonData.result);
    modal.close();
  },
};
