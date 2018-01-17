import ModalSource from './ModalSource';

import { STRINGS } from '../../../config/wagtailConfig';

const $ = global.jQuery;

class ImageSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(imageData) {
    this.onConfirmAtomicBlock({
      id: imageData.id,
      src: imageData.preview.url,
      alt: imageData.alt,
      format: imageData.format,
    });
  }

  componentDidMount() {
    const { onClose } = this.props;

    const imageChooser = global.chooserUrls.imageChooser;
    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url: imageChooser + '?select_format=true',
      responses: {
        imageChosen: this.parseData,
      },
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(STRINGS.SERVER_ERROR);
        onClose();
      },
    });
  }
}

export default ImageSource;
