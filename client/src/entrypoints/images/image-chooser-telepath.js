import { ChooserFactory } from '../../components/ChooserWidget';

class ImageChooserFactory extends ChooserFactory {
  // eslint-disable-next-line no-undef
  widgetClass = ImageChooser;
}
window.telepath.register(
  'wagtail.images.widgets.ImageChooser',
  ImageChooserFactory,
);
