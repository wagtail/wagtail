import $ from 'jquery';
import { initTabs } from '../../includes/tabs';
import { submitCreationForm } from '../../includes/chooserModal';

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
    const form = $('form.task-search', modal.body)[0];

    function ajaxifyLinks(context) {
      $('a.task-choice', context).on('click', function handleClick() {
        modal.loadUrl(this.href);
        return false;
      });

      $('.pagination a', context).on('click', function handleClick() {
        const url = this.href;
        form.dispatchEvent(new CustomEvent('navigate', { detail: { url } }));
        return false;
      });

      // Reinitialize tabs to hook up tab event listeners in the modal
      initTabs();

      // set up success handling when new results are returned for next search
      modal.body[0].addEventListener(
        'w-swap:success',
        ({ srcElement }) => ajaxifyLinks($(srcElement)),
        { once: true },
      );
    }

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
