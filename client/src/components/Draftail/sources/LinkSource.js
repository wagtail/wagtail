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
    let data = entity.getData();

    if (typeof data === 'string') {
      data = { url: data, linkType: 'external', title: '' };
    }

    urlParams.link_text = data.title;

    switch (data.linkType) {
    case 'page':
      url = ` ${pageChooser}${data.parentId}/`;
      break;

    case 'email':
      url = emailLinkChooser;
      urlParams.link_url = data.url.replace('mailto:', '');
      break;

    default:
      url = externalLinkChooser;
      urlParams.link_url = data.url;
      break;
    }
  }

  return { url, urlParams };
};

class LinkSource extends ModalSource {
  constructor(props) {
    super(props);
    this.parseData = this.parseData.bind(this);
  }

  // Plaster over more Wagtail internals.
  parseData(pageData) {
    const data = Object.assign({}, pageData);

    if (data.id) {
      data.linkType = 'page';
    } else if (data.url.indexOf('mailto:') === 0) {
      data.linkType = 'email';
    } else {
      data.linkType = 'external';
    }

    // We do not want each link to have the page's title as an attr.
    // nor links to have the link URL as a title.
    if (data.linkType === 'page' || data.url.replace('mailto:', '') === data.title) {
      delete data.title;
    }

    this.onConfirm(data);
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
