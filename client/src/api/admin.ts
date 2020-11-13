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
    translations?: any;
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

interface GetPageTranslationsOptions {
  fields?: string[];
  onlyWithChildren?: boolean;
  offset?: number;
}
type GetPageTranslations = (id: number, options: GetPageTranslationsOptions) => Promise<WagtailPageListAPI>;
export const getPageTranslations: GetPageTranslations = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES}?translation_of=${id}&limit=20`;

  if (options.fields) {
    url += `&fields=parent,${global.encodeURIComponent(options.fields.join(','))}`;
  } else {
    url += '&fields=parent';
  }

  if (options.onlyWithChildren) {
    url += '&has_children=1';
  }

  if (options.offset) {
    url += `&offset=${options.offset}`;
  }

  return get(url);
};

interface GetAllPageTranslationsOptions {
  fields?: string[];
  onlyWithChildren?: boolean;
}

export const getAllPageTranslations = async (id: number, options: GetAllPageTranslationsOptions) => {
  const items: WagtailPageAPI[] = [];
  let iterLimit = 100;

  for (;;) {
    const page = await getPageTranslations(id, { offset: items.length, ...options });

    page.items.forEach(item => items.push(item));

    if (items.length >= page.meta.total_count || iterLimit-- <= 0) {
      return items;
    }
  }
};
