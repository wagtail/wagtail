import $ from 'jquery';
import { StaticBlockDefinition } from './StaticBlock';

window.$ = $;

window.comments = {
  getContentPath: jest.fn(),
};

describe('telepath: wagtail.blocks.StaticBlock', () => {
  let boundBlock;

  beforeEach(() => {
    // Define a test block
    const blockDef = new StaticBlockDefinition('test_field', {
      text: 'The admin text',
      icon: 'icon',
      label: 'The label',
    });

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'));
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('boundblock matches the snapshot', () => {
    expect(boundBlock).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StaticBlock HTML escaping', () => {
  let boundBlock;

  beforeEach(() => {
    window.somethingBad = jest.fn();

    // Define a test block
    const blockDef = new StaticBlockDefinition('test_field', {
      text: 'The admin text <script>somethingBad();</script>',
      icon: 'icon',
      label: 'The label',
    });

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'));
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test("javascript can't execute", () => {
    expect(window.somethingBad.mock.calls.length).toBe(0);
  });

  test('boundblock matches the snapshot', () => {
    expect(boundBlock).toMatchSnapshot();
  });
});

describe('telepath: wagtail.blocks.StaticBlock allows safe HTML', () => {
  let boundBlock;

  beforeEach(() => {
    window.somethingBad = jest.fn();

    // Define a test block
    const blockDef = new StaticBlockDefinition('test_field', {
      html: 'The admin text <script>somethingBad();</script>',
      icon: 'icon',
      label: 'The label',
    });

    // Render it
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundBlock = blockDef.render($('#placeholder'));
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
  });

  test('javascript can execute', () => {
    expect(window.somethingBad.mock.calls.length).toBe(1);
  });

  test('boundblock matches the snapshot', () => {
    expect(boundBlock).toMatchSnapshot();
  });
});
