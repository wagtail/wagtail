import ModalSource from './ModalSource';

const $ = global.jQuery;

class ImageSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(imageData) {
    this.onConfirmAtomicBlock(Object.assign({}, imageData, {
      src: imageData.preview.url,
    }));
  }

  componentDidMount() {
    const imageChooser = global.chooserUrls.imageChooser;
    $(document.body).on('hidden.bs.modal', this.onClose);

    global.ModalWorkflow({
      url: imageChooser,
      responses: {
        imageChosen: this.parseData,
      },
    });
  }
}

export default ImageSource;
