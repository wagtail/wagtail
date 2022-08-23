/* eslint-disable max-classes-per-file */
import { Application, Controller } from '@hotwired/stimulus';
import { AbstractController } from '../controllers/AbstractController';
import { createController, initStimulus } from './stimulus';

jest.useFakeTimers();

/**
 * Example controller (shortcut method definitions object) from documentation
 */
const wordCountController = {
  STATIC: {
    values: { max: { default: 10, type: Number } },
  },
  connect() {
    this.setupOutput();
    this.updateCount();
  },
  setupOutput() {
    if (this.output) return;
    const template = document.createElement('template');
    template.innerHTML = `<output name='word-count' for='${this.element.id}' style='float: right;'></output>`;
    const output = template.content.firstChild;
    this.element.insertAdjacentElement('beforebegin', output);
    this.output = output;
  },
  updateCount(event) {
    const value = event ? event.target.value : this.element.value;
    const words = (value || '').split(' ');
    this.output.textContent = `${words.length} / ${this.maxValue} words`;
  },
  disconnect() {
    this.output && this.output.remove();
  },
};

/**
 * Example controller from documentation as an ES6 class
 */
class WordCountController extends Controller {
  static values = { max: { default: 10, type: Number } };

  connect() {
    const output = document.createElement('output');
    output.setAttribute('name', 'word-count');
    output.setAttribute('for', this.element.id);
    output.style.float = 'right';
    this.element.insertAdjacentElement('beforebegin', output);
    this.output = output;
    this.updateCount();
  }

  setupOutput() {
    if (this.output) return;
    const template = document.createElement('template');
    template.innerHTML = `<output name='word-count' for='${this.element.id}' style='float: right;'></output>`;
    const output = template.content.firstChild;
    this.element.insertAdjacentElement('beforebegin', output);
    this.output = output;
  }

  updateCount(event) {
    const value = event ? event.target.value : this.element.value;
    const words = (value || '').split(' ');
    this.output.textContent = `${words.length} / ${this.maxValue} words`;
  }

  disconnect() {
    this.output && this.output.remove();
  }
}

describe('initStimulus', () => {
  document.body.innerHTML = `
  <main>
  <section data-controller="w-test-mock">
    <div id="item" data-w-test-mock-target="item"></div>
  </section>
  </main>`;

  const mockControllerConnected = jest.fn();

  class TestMockController extends AbstractController {
    static targets = ['item'];

    connect() {
      mockControllerConnected();
      this.itemTargets.forEach((item) => {
        item.setAttribute('hidden', '');
      });
    }
  }

  const definitions = [
    { identifier: 'w-test-mock', controllerConstructor: TestMockController },
  ];

  let application;

  // note: no Wagtail code should load before this, however it is good to ensure this event fires
  const stimulusInit = jest.fn();
  document.addEventListener('wagtail:stimulus-init', stimulusInit);

  const stimulusReady = jest.fn(({ detail }) => {
    // register example controllers for other tests
    detail.register('example-a', detail.createController(wordCountController));
    detail.register('example-b', WordCountController);
  });

  document.addEventListener('wagtail:stimulus-ready', stimulusReady);

  it('should initialise a stimulus application', () => {
    expect(mockControllerConnected).not.toHaveBeenCalled();
    expect(stimulusInit).not.toHaveBeenCalled();
    expect(stimulusReady).not.toHaveBeenCalled();

    application = initStimulus({ debug: false, definitions });

    expect(application).toBeInstanceOf(Application);
  });

  it('should dispatch init events', () => {
    document.dispatchEvent(new CustomEvent('readystatechange')); // mimic readystatechange
    document.dispatchEvent(new CustomEvent('DOMContentLoaded')); // mimic DOM load

    expect(stimulusInit).toHaveBeenCalledTimes(1);
    expect(stimulusReady).toHaveBeenCalledTimes(2);
  });

  it('should have set the debug value based on the option provided', () => {
    expect(application.debug).toEqual(false);
  });

  it('should have loaded the controller definitions supplied', () => {
    expect(mockControllerConnected).toHaveBeenCalled();
    expect(application.controllers).toHaveLength(1);
    expect(application.controllers[0]).toBeInstanceOf(TestMockController);
  });

  it('should support the ability to enable debug via an event', () => {
    // mock for tests while checking debugging behaviour
    window.console.groupCollapsed = jest.fn();
    window.console.log = jest.fn();

    expect(application.debug).toBe(false);

    document.dispatchEvent(
      new CustomEvent('wagtail:stimulus-enable-debug', { bubbles: true }),
    );

    expect(application.debug).toBe(true);

    application.debug = false; // reset for any tests added after
  });

  it('should support the documented approach for registering a controller via an object with the wagtail:stimulus-ready event', async () => {
    const section = document.createElement('section');
    section.id = 'example-a';
    section.innerHTML = `<input value="some words" id="example-a-input" data-controller="example-a" data-action="change->example-a#updateCount" />`;

    // before controller element added - should not include an `output` element
    expect(document.querySelector('#example-a > output')).toEqual(null);

    document.querySelector('section').after(section);

    await Promise.resolve({});

    // after controller connected - should have an output element
    expect(document.querySelector('#example-a > output').innerHTML).toEqual(
      '2 / 10 words',
    );

    await Promise.resolve({});

    // should respond to changes on the input
    const input = document.querySelector('#example-a > input');
    input.setAttribute('value', 'even more words');
    input.dispatchEvent(new Event('change'));

    expect(document.querySelector('#example-a > output').innerHTML).toEqual(
      '3 / 10 words',
    );

    // removal of the input should also remove the output (disconnect method)
    input.remove();

    await Promise.resolve({});

    // should call the disconnect method (removal of the injected HTML)
    expect(document.querySelector('#example-a > output')).toEqual(null);

    // clean up
    section.remove();
  });

  it('should support the documented approach for registering a controller via a class with the wagtail:stimulus-ready event', async () => {
    const section = document.createElement('section');
    section.id = 'example-b';
    section.innerHTML = `<input value="some words" id="example-b-input" data-controller="example-b" data-action="change->example-b#updateCount" data-example-b-max-value="5" />`;

    // before controller element added - should not include an `output` element
    expect(document.querySelector('#example-b > output')).toEqual(null);

    document.querySelector('section').after(section);

    await Promise.resolve({});

    // after controller connected - should have an output element
    expect(document.querySelector('#example-b > output').innerHTML).toEqual(
      '2 / 5 words',
    );

    await Promise.resolve({});

    // should respond to changes on the input
    const input = document.querySelector('#example-b > input');
    input.setAttribute('value', 'even more words');
    input.dispatchEvent(new Event('change'));

    expect(document.querySelector('#example-b > output').innerHTML).toEqual(
      '3 / 5 words',
    );

    // removal of the input should also remove the output (disconnect method)
    input.remove();

    await Promise.resolve({});

    // should call the disconnect method (removal of the injected HTML)
    expect(document.querySelector('#example-b > output')).toEqual(null);

    // clean up
    section.remove();
  });
});

describe('createController', () => {
  it('should safely create a Stimulus Controller class if no args provided', () => {
    const CustomController = createController();
    expect(CustomController.prototype instanceof Controller).toBeTruthy();
  });

  it('should create a Stimulus Controller class with static properties', () => {
    const someMethod = jest.fn();

    const CustomController = createController({
      STATIC: { targets: ['source'] },
      someMethod,
    });

    expect(CustomController.targets).toEqual(['source']);
    expect(CustomController.someMethod).toBeUndefined();
    expect(CustomController.prototype.someMethod).toEqual(someMethod);
  });
});
