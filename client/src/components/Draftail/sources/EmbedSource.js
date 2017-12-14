import ModalSource from './ModalSource';

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
    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url: global.chooserUrls.embedsChooser,
      responses: {
        embedChosen: this.parseData,
      },
    });
  }
}

export default EmbedSource;
