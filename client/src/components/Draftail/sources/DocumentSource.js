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
    });
  }

  componentDidMount() {
    const { entity } = this.props;
    const documentChooser = global.chooserUrls.documentChooser;
    const url = documentChooser;

    $(document.body).on('hidden.bs.modal', this.onClose);

    // TODO: wagtail should support passing params to this endpoint.
    if (entity) {
      // const entityData = entity.getData();
      // console.log(entityData);
      // if (entityData.title) {
      //   url = url + `?q=${entityData.title}`
      // }
    }

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
