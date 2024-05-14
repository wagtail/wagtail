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
    const data = { _args: ['...'], _type: 'wagtail.blocks.StreamBlock' };

    await setup(
      `<div
        id="my-element"
        data-controller="w-block"
        data-w-block-data-value='${JSON.stringify(data)}'
        >
      </div>`,
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
    const data = { _args: ['...'], _type: 'wagtail.blocks.StreamBlock' };
    const initialData = [{ type: 'paragraph_block', value: '...' }];
    const errorData = { messages: ['An error...'] };

    await setup(
      `<div
        id="my-element"
        data-controller="w-block"
        data-w-block-arguments-value='${JSON.stringify([initialData, errorData])}'
        data-w-block-data-value='${JSON.stringify(data)}'
        >
      </div>`,
    );

    expect(errors).toHaveLength(0);
    expect(unpack).toHaveBeenCalledWith(data);
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
    expect(errors).toHaveProperty(
      '0.error.message',
      'Controlled element needs an id attribute.',
    );
  });

  it('should throw an error if Telepath is not available in the window global', async () => {
    delete window.telepath;
    await setup('<div id="my-element" data-controller="w-block"></div>');

    expect(errors).toHaveLength(1);
    expect(errors).toHaveProperty(
      '0.error.message',
      '`window.telepath` is not available.',
    );
  });
});
