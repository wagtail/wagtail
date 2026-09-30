import { getExplorerPage } from './admin';
import client from './client';

jest.mock('./client', () => ({
  __esModule: true,
  default: {
    get: jest.fn(() =>
      Promise.resolve({
        page: {},
        translations: [],
        children: { count: 0, items: [] },
      }),
    ),
  },
}));

describe('admin API', () => {
  describe('getExplorerPage', () => {
    it('works', () => {
      getExplorerPage(3);
      expect(client.get).toHaveBeenCalledWith('/admin/api/explorer/3/');
    });

    it('#offset', () => {
      getExplorerPage(3, { offset: 20 });
      expect(client.get).toHaveBeenCalledWith(
        '/admin/api/explorer/3/?offset=20',
      );
    });
  });

  afterEach(() => {
    client.get.mockClear();
  });
});
