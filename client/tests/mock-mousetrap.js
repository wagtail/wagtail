jest.mock('mousetrap/plugins/pause/mousetrap-pause', () => ({}));
jest.mock('mousetrap/plugins/global-bind/mousetrap-global-bind', () => ({}));

jest.mock('mousetrap', () => ({
  __esModule: true,
  default: { bind: jest.fn(), globalBind: jest.fn(), pause: jest.fn() },
}));
