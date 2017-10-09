import { ADMIN_API } from '../config/wagtailConfig';
import { getPageChildren, getPage } from './admin';
import * as client from './client';

const stubResult = {
  __types: {
    test: {
      verbose_name: 'Test',
    },
  },
  items: [
    { meta: { type: 'test' } },
    { meta: { type: 'foo' } },
  ],
};

client.get = jest.fn(() => Promise.resolve(stubResult));

describe('admin API', () => {
  describe('getPageChildren', () => {
    it('works', () => {
      getPageChildren(3);
      expect(client.get).toBeCalledWith(`${ADMIN_API.PAGES}?child_of=3`);
    });

    it('#fields', () => {
      getPageChildren(3, { fields: ['title', 'latest_revision_created_at'] });
      // eslint-disable-next-line max-len
      expect(client.get).toBeCalledWith(`${ADMIN_API.PAGES}?child_of=3&fields=title%2Clatest_revision_created_at`);
    });

    it('#onlyWithChildren', () => {
      getPageChildren(3, { onlyWithChildren: true });
      expect(client.get).toBeCalledWith(`${ADMIN_API.PAGES}?child_of=3&has_children=1`);
    });

    it('#offset', () => {
      getPageChildren(3, { offset: 5 });
      expect(client.get).toBeCalledWith(`${ADMIN_API.PAGES}?child_of=3&offset=5`);
    });
  });

  describe('getPage', () => {
    it('should return a result by with a default id argument', () => {
      getPage(3);
      expect(client.get).toBeCalledWith(`${ADMIN_API.PAGES}3/`);
    });
  });

  afterEach(() => {
    client.get.mockClear();
  });
});
