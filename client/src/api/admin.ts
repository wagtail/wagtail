import { get } from '../api/client';

import { ADMIN_API } from '../config/wagtailConfig';

export interface WagtailPageAPI {
  id: number;
  meta: {
    status: {
      status: string;
      live: boolean;
      /* eslint-disable-next-line camelcase */
      has_unpublished_changes: boolean;
    }
    children: any;
    parent: {
      id: number;
    } | null;
    locale?: string;
  };
  /* eslint-disable-next-line camelcase */
  admin_display_title?: string;
}

interface WagtailPageListAPI {
  meta: {
    /* eslint-disable-next-line camelcase */
    total_count: number;
  };
  items: WagtailPageAPI[];
}

export const getPage: (id: number) => Promise<WagtailPageAPI> = (id) => {
  const url = `${ADMIN_API.PAGES}${id}/`;

  return get(url);
};

interface GetPageChildrenOptions {
  fields?: string[];
  onlyWithChildren?: boolean;
  offset?: number;
}

type GetPageChildren = (id: number, options: GetPageChildrenOptions) => Promise<WagtailPageListAPI>;
export const getPageChildren: GetPageChildren = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES}?child_of=${id}&for_explorer=1`;

  if (options.fields) {
    url += `&fields=parent,${window.encodeURIComponent(options.fields.join(','))}`;
  } else {
    url += '&fields=parent';
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
