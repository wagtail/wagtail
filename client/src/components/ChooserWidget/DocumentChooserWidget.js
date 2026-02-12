/* global DocumentChooserModal */

import { Chooser, ChooserFactory } from '.';

export class DocumentChooser extends Chooser {
  chooserModalClass = DocumentChooserModal;
}
window.DocumentChooser = DocumentChooser;

export class DocumentChooserFactory extends ChooserFactory {
  widgetClass = DocumentChooser;
  chooserModalClass = DocumentChooserModal;
}
