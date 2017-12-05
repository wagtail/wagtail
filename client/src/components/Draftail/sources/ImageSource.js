import ModalSource from './ModalSource';

const $ = global.jQuery;
const ModalWorkflow = global.ModalWorkflow;

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

    // eslint-disable-next-line new-cap
    ModalWorkflow({
      url: imageChooser,
      responses: {
        imageChosen: this.parseData,
      },
    });
  }
}

export default ImageSource;
