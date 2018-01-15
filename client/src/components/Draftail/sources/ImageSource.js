import ModalSource from './ModalSource';

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
    const imageChooser = global.chooserUrls.imageChooser;
    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url: imageChooser + '?select_format=true',
      responses: {
        imageChosen: this.parseData,
      },
    });
  }
}

export default ImageSource;
