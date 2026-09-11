import { WAGTAIL_CONFIG } from '../config/wagtailConfig';
import { getPage, getPageChildren, getPageTranslations } from './admin';
import client from './client';

const { ADMIN_API } = WAGTAIL_CONFIG;

jest.mock('./client', () => {
  const stubResult = {
    count: 2,
    items: [
      { id: 1, meta: { type: 'test' } },
      { id: 2, meta: { type: 'foo' } },
    ],
  };

  return {
    __esModule: true,
    default: { get: jest.fn(() => Promise.resolve(stubResult)) },
  };
});

describe('admin API', () => {
  describe('getPageChildren', () => {
    it('works', () => {
      getPageChildren(3);
      expect(client.get).toHaveBeenCalledWith(
        `${ADMIN_API.PAGES_EXPLORE}?child_of=3`,
      );
    });

    it('#offset', () => {
      getPageChildren(3, { offset: 5 });
      expect(client.get).toHaveBeenCalledWith(
        `${ADMIN_API.PAGES_EXPLORE}?child_of=3&offset=5`,
      );
    });
  });

  describe('getPage', () => {
    it('should return a result by with a default id argument', () => {
      getPage(3);
      expect(client.get).toHaveBeenCalledWith(`${ADMIN_API.PAGES}3/`);
    });
  });

  describe('getPageTranslations', () => {
    it('works', () => {
      getPageTranslations(3);
      expect(client.get).toHaveBeenCalledWith(
        `${ADMIN_API.PAGES}?translation_of=3&limit=20&has_children=true`,
      );
    });

    it('#offset', () => {
      getPageTranslations(3, { offset: 5 });
      expect(client.get).toHaveBeenCalledWith(
        `${ADMIN_API.PAGES}?translation_of=3&limit=20&has_children=true&offset=5`,
      );
    });
  });

  afterEach(() => {
    client.get.mockClear();
  });
});
