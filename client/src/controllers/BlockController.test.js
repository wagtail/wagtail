import { Application } from '@hotwired/stimulus';
import { BlockController } from './BlockController';

const render = jest.fn();
const unpack = jest.fn(() => ({ render }));
window.telepath = { unpack };

describe('BlockController', () => {
  const eventNames = ['w-block:ready'];

  const events = {};

  eventNames.forEach((name) => {
    document.addEventListener(name, (event) => {
      events[name].push(event);
    });
  });

  let application;
  let errors = [];

  const setup = (html, { identifier = 'w-block' } = {}) => {
    document.body.innerHTML = `<main>${html}</main>`;

    application = new Application();

    application.register(identifier, BlockController);

    application.handleError = (error, message) => {
      errors.push({ error, message });
    };

    application.start();

    return Promise.resolve();
  };

  beforeEach(() => {
    application?.stop();
    document.body.innerHTML = '';
    errors = [];
    eventNames.forEach((name) => {
      events[name] = [];
    });
    jest.clearAllMocks();
  });

  it('does nothing if block element is not found', async () => {
    await setup('<div></div>');

    expect(errors).toHaveLength(0);

    expect(unpack).not.toHaveBeenCalled();

    expect(events['w-block:ready']).toHaveLength(0);
  });

  it('should render block if element is controlled', async () => {
    const data = { name: 'John Doe' };

    await setup(
      `<div id="my-element" data-controller="w-block" data-w-block-data-value='${JSON.stringify({ name: 'John Doe' })}'></div>`,
    );

    expect(errors).toHaveLength(0);
    expect(unpack).toHaveBeenCalledWith(data);
    expect(render).toHaveBeenCalledWith(
      document.getElementById('my-element'),
      'my-element',
    );
    expect(events['w-block:ready']).toHaveLength(1);
  });

  it('should call the unpacked render function with provided initial & error data', async () => {
    const initialData = ['Hello', 'World'];
    const errorData = { message: 'Something went wrong' };
    const argumentsValue = [initialData, errorData];

    await setup(
      `<div id="my-element" data-controller="w-block" data-w-block-arguments-value='${JSON.stringify(argumentsValue)}' data-w-block-data-value='{"name":"John Doe"}'></div>`,
    );

    expect(errors).toHaveLength(0);
    expect(unpack).toHaveBeenCalledWith({ name: 'John Doe' });
    expect(render).toHaveBeenCalledWith(
      document.getElementById('my-element'),
      'my-element',
      initialData,
      errorData,
    );
    expect(events['w-block:ready']).toHaveLength(1);
  });

  it('should throw an error if used on an element without an id', async () => {
    await setup('<div data-controller="w-block"></div>');

    expect(errors).toHaveLength(1);
  });

  it('should throw an error if Telepath is not available in the window global', async () => {
    delete window.telepath;
    await setup('<div id="my-element" data-controller="w-block"></div>');

    expect(errors).toHaveLength(1);
  });
});
