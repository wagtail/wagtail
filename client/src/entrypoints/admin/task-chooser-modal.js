import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import {
  submitCreationForm,
  SearchController,
} from '../../includes/chooserModal';

const ajaxifyTaskCreateTab = (modal) => {
  $(
    '#tab-new a.task-type-choice, #tab-new a.choose-different-task-type',
    modal.body,
  ).on('click', function onClickNew() {
    modal.loadUrl(this.href);
    return false;
  });

  // eslint-disable-next-line func-names
  $('form.task-create', modal.body).on('submit', function () {
    submitCreationForm(modal, this, { errorContainerSelector: '#tab-new' });

    return false;
  });
};

const TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = {
  chooser(modal, jsonData) {
    function ajaxifyLinks(context) {
      $('a.task-choice', context)
        // eslint-disable-next-line func-names
        .on('click', function () {
          modal.loadUrl(this.href);
          return false;
        });

      // eslint-disable-next-line func-names
      $('.pagination a', context).on('click', function () {
        // eslint-disable-next-line @typescript-eslint/no-use-before-define
        searchController.fetchResults(this.href);
        return false;
      });

      // Reinitialize tabs to hook up tab event listeners in the modal
      initTabs();
    }

    const searchController = new SearchController({
      form: $('form.task-search', modal.body),
      containerElement: modal.body,
      resultsContainerSelector: '#search-results',
      onLoadResults: (context) => {
        ajaxifyLinks(context);
      },
      inputDelay: 50,
    });
    searchController.attachSearchInput('#id_q');
    searchController.attachSearchFilter('#id_task_type');

    ajaxifyLinks(modal.body);
    ajaxifyTaskCreateTab(modal, jsonData);
  },
  task_chosen(modal, jsonData) {
    modal.respond('taskChosen', jsonData.result);
    modal.close();
  },
  reshow_create_tab(modal, jsonData) {
    $('#tab-new', modal.body).html(jsonData.htmlFragment);
    ajaxifyTaskCreateTab(modal, jsonData);
  },
};
window.TASK_CHOOSER_MODAL_ONLOAD_HANDLERS = TASK_CHOOSER_MODAL_ONLOAD_HANDLERS;
