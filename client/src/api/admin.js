import { get } from '../api/client';

import { ADMIN_API } from '../config/wagtail';

export const getChildPages = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES}?child_of=${id}`;

  if (options.fields) {
    url += `&fields=${global.encodeURIComponent(options.fields.join(','))}`;
  }

  if (options.filter) {
    url += `&${options.filter}`;
  }

  return get(url).then(res => res.body);
};

export const getPage = (id) => {
  const url = `${ADMIN_API.PAGES}${id}/`;

  return get(url).then(res => res.body);
};
