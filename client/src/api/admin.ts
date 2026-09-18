import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import client from './client';

const { ADMIN_API } = WAGTAIL_CONFIG;

export interface WagtailPageAPI {
  id: number;
  admin_display_title?: string;

  meta: {
    type?: string;
    parent: {
      id: number;
    } | null;
    children?: {
      count: number;
    };

    locale?: string;

    live: boolean;
    has_unpublished_changes: boolean;
    status: string;
  };
}

interface WagtailPageListAPI {
  count: number;
  items: WagtailPageAPI[];
}

export const getPage: (id: number) => Promise<WagtailPageAPI> = (id) => {
  const url = `${ADMIN_API.PAGES}${id}/`;

  return client.get(url);
};

interface GetPageChildrenOptions {
  offset?: number;
}

type GetPageChildren = (
  id: number,
  options?: GetPageChildrenOptions,
) => Promise<WagtailPageListAPI>;
export const getPageChildren: GetPageChildren = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES_EXPLORE}?child_of=${id}`;

  if (options.offset) {
    url += `&offset=${options.offset}`;
  }

  url += ADMIN_API.EXTRA_CHILDREN_PARAMETERS;

  return client.get(url);
};

interface GetPageTranslationsOptions {
  offset?: number;
}

type GetPageTranslations = (
  id: number,
  options?: GetPageTranslationsOptions,
) => Promise<WagtailPageListAPI>;
export const getPageTranslations: GetPageTranslations = (id, options = {}) => {
  let url = `${ADMIN_API.PAGES}?translation_of=${id}&limit=20&has_children=true`;

  if (options.offset) {
    url += `&offset=${options.offset}`;
  }

  return client.get(url);
};

export const getAllPageTranslations = async (
  id: number,
): Promise<WagtailPageAPI[]> => {
  const items: WagtailPageAPI[] = [];
  let iterLimit = 100;

  for (;;) {
    // eslint-disable-next-line no-await-in-loop
    const page = await getPageTranslations(id, {
      offset: items.length,
    });

    page.items.forEach((item) => items.push(item));

    // eslint-disable-next-line no-plusplus
    if (items.length >= page.count || iterLimit-- <= 0) {
      return items;
    }
  }
};
