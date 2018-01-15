import ModalSource from './ModalSource';

const $ = global.jQuery;

// Plaster over Wagtail internals.
const buildInitialUrl = (entity, openAtParentId, canChooseRoot, pageTypes) => {
  // We can't destructure from the window object yet
  const pageChooser = global.chooserUrls.pageChooser;
  const emailLinkChooser = global.chooserUrls.emailLinkChooser;
  const externalLinkChooser = global.chooserUrls.externalLinkChooser;
  let url = pageChooser;

  if (openAtParentId) {
    url = `${url}${openAtParentId}/`;
  }

  const urlParams = {
    page_type: pageTypes.join(','),
    allow_external_link: true,
    allow_email_link: true,
    can_choose_root: canChooseRoot ? 'true' : 'false',
    link_text: '',
  };

  if (entity) {
    const data = entity.getData();

    // urlParams.link_text = data.title;

    if (data.id) {
      url = ` ${pageChooser}${data.parentId}/`;
    } else if (data.url.startsWith('mailto:')) {
      url = emailLinkChooser;
      urlParams.link_url = data.url.replace('mailto:', '');
    } else {
      url = externalLinkChooser;
      urlParams.link_url = data.url;
    }
  }

  return { url, urlParams };
};

class LinkSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  parseData(data) {
    const parsedData = {
      url: data.url,
    };

    if (data.id) {
      parsedData.id = data.id;
      parsedData.parentId = data.parentId;
    }

    this.onConfirm(parsedData);
  }

  componentDidMount() {
    const { entity } = this.props;
    const openAtParentId = false;
    const canChooseRoot = false;
    const pageTypes = ['wagtailcore.page'];
    const { url, urlParams } = buildInitialUrl(entity, openAtParentId, canChooseRoot, pageTypes);

    $(document.body).on('hidden.bs.modal', this.onClose);

    // eslint-disable-next-line new-cap
    window.ModalWorkflow({
      url,
      urlParams,
      responses: {
        pageChosen: this.parseData,
      },
    });
  }
}

export default LinkSource;
