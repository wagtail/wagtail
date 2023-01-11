import { ChooserFactory } from '../../components/ChooserWidget';

class PageChooserFactory extends ChooserFactory {
  // eslint-disable-next-line no-undef
  widgetClass = PageChooser;
}
window.telepath.register('wagtail.widgets.PageChooser', PageChooserFactory);
