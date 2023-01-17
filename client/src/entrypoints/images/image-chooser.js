import { ImageChooser } from '../../components/ChooserWidget/ImageChooserWidget';

window.ImageChooser = ImageChooser;

function createImageChooser(id) {
  /* RemovedInWagtail50Warning */
  return new ImageChooser(id);
}

window.createImageChooser = createImageChooser;
