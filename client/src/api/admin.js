import { get } from '../api/client';

import { ADMIN_API } from '../config/wagtailConfig';

export class PagesAPI {
  constructor(endpointUrl, extraChildParams = '') {
    this.endpointUrl = endpointUrl;
    this.extraChildParams = extraChildParams;
  }

  getPage(id) {
    const url = `${this.endpointUrl}${id}/`;
    return get(url);
  }

  getPageChildren(id, options = {}) {
    let url = `${this.endpointUrl}?child_of=${id}`;

    if (options.fields) {
      url += `&fields=${global.encodeURIComponent(options.fields.join(','))}`;
    }

    if (options.onlyWithChildren) {
      url += '&has_children=1';
    }

    if (options.offset) {
      url += `&offset=${options.offset}`;
    }

    url += this.extraChildParams;

    return get(url);
  }
}

export const getPage = (id) => {
  const api = new PagesAPI(ADMIN_API.PAGES, ADMIN_API.EXTRA_CHILDREN_PARAMETERS);
  return api.getPage(id);
};

export const getPageChildren = (id, options = {}) => {
  const api = new PagesAPI(ADMIN_API.PAGES, ADMIN_API.EXTRA_CHILDREN_PARAMETERS);
  return api.getPageChildren(id, options);
};
