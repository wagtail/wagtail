import { Chooser, ChooserFactory } from '.';

export class DocumentChooser extends Chooser {
  // eslint-disable-next-line no-undef
  chooserModalClass = DocumentChooserModal;
}
window.DocumentChooser = DocumentChooser;

export class DocumentChooserFactory extends ChooserFactory {
  widgetClass = DocumentChooser;
  // eslint-disable-next-line no-undef
  chooserModalClass = DocumentChooserModal;
}
