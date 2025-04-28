import { ChooserModal } from '../../includes/chooserModal';
import { Chooser, ChooserFactory } from '.';

class SnippetChooserModal extends ChooserModal {
  // left as is for backwards compatibility.
}

export class SnippetChooser extends Chooser {
  titleStateKey = 'string';
  chooserModalClass = SnippetChooserModal;
}

export class SnippetChooserFactory extends ChooserFactory {
  widgetClass = SnippetChooser;
  chooserModalClass = SnippetChooserModal;
}
