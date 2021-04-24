const jQueryObj = {
  on: jest.fn(),
  off: jest.fn(),
};

global.jQuery = () => jQueryObj;
