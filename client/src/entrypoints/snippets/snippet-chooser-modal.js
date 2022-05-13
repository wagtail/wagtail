import { ChooserModalOnloadHandlerFactory } from '../../includes/chooserModal';

window.SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new ChooserModalOnloadHandlerFactory({
    chosenLinkSelector: 'a.snippet-choice',
    searchFormSelector: 'form.snippet-search',
    searchFilterSelectors: ['#snippet-chooser-locale'],
    chosenResponseName: 'snippetChosen',
  }).getOnLoadHandlers();
