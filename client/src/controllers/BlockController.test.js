import { Application } from '@hotwired/stimulus';
import { BlockController } from './BlockController'; // Replace with your controller path

describe('BlockController', () => {
  let application;

  const setup = async (html) => {
    document.body.innerHTML = html;
    application = new Application();
    application.register('w-block', BlockController);

    await Promise.resolve(); // Ensure Stimulus is initialized
  };

  afterEach(() => {
    document.body.innerHTML = ''; // Clean up the HTML after each test
  });

  it('executes afterLoad method and renders block widget', async () => {
    const html = `
      <div id="testBlock" data-block></div>
    `;

    await setup(html);

    // Mocking the necessary data attributes
    const body = document.querySelector('#testBlock');
    body.dataset.wBlockDataValue = JSON.stringify({ data: 'testData' });
    body.dataset.wBlockInitialValue = JSON.stringify({ value: 'testValue' });
    body.dataset.wBlockErrorValue = JSON.stringify({ error: 'testError' });

    // Mocking window.telepath
    const mockTelepath = {
      unpack: jest.fn().mockReturnValue({
        render: jest.fn(),
      }),
    };
    Object.defineProperty(window, 'telepath', {
      value: mockTelepath,
    });

    // Call the static afterLoad method
    BlockController.afterLoad();

    // Expectations
    expect(window.initBlockWidget).toBeDefined(); // Ensure initBlockWidget is defined
    expect(window.initBlockWidget).toBeInstanceOf(Function); // Ensure initBlockWidget is a function

    // Call the mocked initBlockWidget function
    window.initBlockWidget('testBlock');

    // Expectations for rendering the block widget
    expect(document.querySelector('#testBlock')).not.toBeNull(); // Ensure the block element still exists
    expect(mockTelepath.unpack).toHaveBeenCalledTimes(1); // Ensure telepath.unpack is called once
    expect(mockTelepath.unpack).toHaveBeenCalledWith({ data: 'testData' }); // Expect the correct data to be passed to telepath.unpack
    expect(mockTelepath.unpack().render).toHaveBeenCalledTimes(1); // Ensure render method is called once
    expect(mockTelepath.unpack().render).toHaveBeenCalledWith(
      body,
      'testBlock',
      { value: 'testValue' }, // Expect the correct value to be passed to render
      { error: 'testError' }, // Expect the correct error to be passed to render
    );
  });

  it('does nothing if block element is not found', async () => {
    // Call the static afterLoad method
    BlockController.afterLoad();

    // Call the mocked initBlockWidget function with an invalid id
    window.initBlockWidget('invalidBlockId');

    // Expectations
    expect(document.querySelector('#invalidBlockId')).toBeNull(); // Ensure the block element doesn't exist
    // Add more expectations as needed
  });
});
