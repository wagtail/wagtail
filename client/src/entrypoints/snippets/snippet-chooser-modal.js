import { ChooserModalOnloadHandlerFactory } from '../../includes/chooserModal';

window.SNIPPET_CHOOSER_MODAL_ONLOAD_HANDLERS =
  new ChooserModalOnloadHandlerFactory({
    chosenResponseName: 'snippetChosen',
  }).getOnLoadHandlers();
