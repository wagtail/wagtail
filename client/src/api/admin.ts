import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import client from './client';

const { ADMIN_API } = WAGTAIL_CONFIG;

interface WagtailSimplePageAPI {
  id: number;
  title: string;
  meta: {
    type: string;
  };
}

export interface WagtailPageAPI {
  id: number;
  title: string;
  admin_display_title: string;
  meta: {
    type: string;
    locale: string;
    depth: number;
    status: string;
    live: boolean;
    has_unpublished_changes: boolean;
    has_children: boolean;
    // Only available for the explorer's current page
    parent?: WagtailSimplePageAPI | null;
  };
}

export interface WagtailExplorerAPI {
  page: WagtailPageAPI;
  translations: Array<{
    id: number;
    locale: string;
  }>;
  children: {
    count: number;
    items: WagtailPageAPI[];
  };
}

interface GetExplorerPageOptions {
  offset?: number;
}

/**
 * Gets a page, its translations, and its children for the page explorer.
 */
export const getExplorerPage = (
  id: number,
  options: GetExplorerPageOptions = {},
): Promise<WagtailExplorerAPI> => {
  let url = ADMIN_API.EXPLORER.replace('999999', String(id));

  if (options.offset) {
    url += `?offset=${options.offset}`;
  }

  return client.get(url);
};
