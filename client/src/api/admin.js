import { get } from '../api/client';

import { ADMIN_API } from '../config/wagtailConfig';


export const getPage = (id) => {
  const url = `${ADMIN_API.PAGES}${id}/`;

  return get(url);
};

export const getPageChildren = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES}?child_of=${id}`;

  if (options.fields) {
    url += `&fields=${global.encodeURIComponent(options.fields.join(','))}`;
  }

  if (options.onlyWithChildren) {
    url += '&has_children=1';
  }

  if (options.offset) {
    url += `&offset=${options.offset}`;
  }

  url += ADMIN_API.EXTRA_CHILDREN_PARAMETERS;

  return get(url);
};
