import ModalSource from './ModalSource';

import { STRINGS } from '../../../config/wagtailConfig';

const $ = global.jQuery;

class EmbedSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(html, embed) {
    this.onConfirmAtomicBlock({
      embedType: embed.embedType,
      url: embed.url,
      providerName: embed.providerName,
      authorName: embed.authorName,
      thumbnail: embed.thumbnail,
      title: embed.title,
    });
  }

  componentDidMount() {
    const { onClose } = this.props;

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url: global.chooserUrls.embedsChooser,
      responses: {
        embedChosen: this.parseData,
      },
      onError: () => {
        // eslint-disable-next-line no-alert
        window.alert(STRINGS.SERVER_ERROR);
        onClose();
      },
    });
  }
}

export default EmbedSource;
