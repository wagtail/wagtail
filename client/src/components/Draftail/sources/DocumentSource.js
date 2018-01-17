import ModalSource from './ModalSource';

const $ = global.jQuery;

class DocumentSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(data) {
    this.onConfirm({
      id: data.id,
      url: data.url,
    }, data.title);
  }

  componentDidMount() {
    const documentChooser = global.chooserUrls.documentChooser;
    const url = documentChooser;

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url,
      responses: {
        documentChosen: this.parseData,
      },
    });
  }
}

export default DocumentSource;
