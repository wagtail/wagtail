import ModalSource from './ModalSource';

import { STRINGS } from '../../../config/wagtailConfig';

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
    const { onClose } = this.props;
    const documentChooser = global.chooserUrls.documentChooser;
    const url = documentChooser;

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url,
      responses: {
        documentChosen: this.parseData,
      },
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(STRINGS.SERVER_ERROR);
        onClose();
      },
    });
  }
}

export default DocumentSource;
