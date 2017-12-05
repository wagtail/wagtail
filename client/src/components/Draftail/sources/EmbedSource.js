import ModalSource from './ModalSource';

const $ = global.jQuery;

class EmbedSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(html) {
    const embed = $.parseHTML(html)[0];

    this.onConfirmAtomicBlock({
      embedType: embed.getAttribute('data-embedtype'),
      url: embed.getAttribute('data-url'),
      providerName: embed.getAttribute('data-provider-name'),
      authorName: embed.getAttribute('data-author-name'),
      thumbnail: embed.getAttribute('data-thumbnail-url'),
      title: embed.getAttribute('data-title'),
    });
  }

  componentDidMount() {
    $(document.body).on('hidden.bs.modal', this.onClose);

    global.ModalWorkflow({
      url: global.chooserUrls.embedsChooser,
      responses: {
        embedChosen: this.parseData,
      },
    });
  }
}

export default EmbedSource;
