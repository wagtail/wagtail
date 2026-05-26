import { BlockToolbar, InlineToolbar } from 'draftail';
import React from 'react';

import draftail, {
  Document,
  EmbedBlock,
  ImageBlock,
  Link,
  wrapWagtailIcon,
} from './index';

window.comments = {
  getContentPath: jest.fn(),
};

const findComponent = (children, type) => {
  const components = React.Children.toArray(children);
  let component = components.find((child) => child.type === type);

  if (component) {
    return component;
  }

  components.some((child) => {
    component = findComponent(child.props?.children, type);
    return Boolean(component);
  });

  return component;
};

const getTopToolbarComponents = (
  props = {},
  html = '<input id="test" value="null" />',
) => {
  document.body.innerHTML = html;
  const field = document.querySelector('#test');
  const toolbarProps = {
    onChange: jest.fn(),
    onCompleteSource: jest.fn(),
    onRequestSource: jest.fn(),
    addHR: jest.fn(),
    ...props,
  };

  draftail.initEditor('#test', {});

  const topToolbar = field.draftailEditor.props.topToolbar(toolbarProps);
  const toolbarComponents = React.Children.toArray(topToolbar.props.children);
  const blockToolbarWrapper = toolbarComponents.find((component) =>
    findComponent(component.props?.children, BlockToolbar),
  );

  return {
    toolbarProps,
    blockToolbarWrapper,
    blockToolbar: findComponent(topToolbar.props.children, BlockToolbar),
    inlineToolbar: findComponent(topToolbar.props.children, InlineToolbar),
  };
};

const setWindowScroll = ({ top = 0, left = 0 }) => {
  Object.defineProperty(window, 'scrollY', {
    configurable: true,
    value: top,
  });
  Object.defineProperty(window, 'scrollX', {
    configurable: true,
    value: left,
  });
};

describe('Draftail', () => {
  describe('#initEditor', () => {
    beforeEach(() => {
      document.head.innerHTML = '';
      document.body.innerHTML = '';
    });

    it('works', () => {
      document.body.innerHTML = '<input type="text" id="test" value="null" />';
      const field = document.querySelector('#test');

      draftail.initEditor('#test', {});

      expect(field.draftailEditor).toBeDefined();
    });

    it('onSave', () => {
      document.body.innerHTML = '<input id="test" value="null" />';
      const field = document.querySelector('#test');

      draftail.initEditor('#test', {});

      field.draftailEditor.saveState();

      expect(field.value).toBe('null');
    });

    it('options', () => {
      document.body.innerHTML = '<input id="test" value="null" />';
      const field = document.querySelector('#test');

      draftail.registerPlugin(
        {
          type: 'IMAGE',
          source: () => {},
          block: () => null,
        },
        'entityTypes',
      );

      draftail.registerPlugin(
        {
          type: 'sentences',
          meta: () => null,
        },
        'controls',
      );

      draftail.registerPlugin(
        {
          type: 'punctuation',
          strategy: () => {},
          component: () => null,
        },
        'decorators',
      );

      draftail.registerPlugin(
        {
          type: 'anchorify',
          handlePastedText: () => 'not-handled',
        },
        'plugins',
      );

      draftail.initEditor('#test', {
        entityTypes: [{ type: 'IMAGE' }],
        controls: [{ type: 'sentences' }],
        decorators: [{ type: 'punctuation' }],
        plugins: [{ type: 'anchorify' }],
        enableHorizontalRule: true,
      });

      expect(field.draftailEditor.props).toMatchSnapshot();
      // Make sure we don’t initialise a character count on fields that have the default unlimited max length.
      expect(field.draftailEditor.props.ariaDescribedBy).toBe(null);
    });

    it('maxLength', () => {
      document.body.innerHTML =
        '<input id="test" value="null" maxlength="50" />';
      const field = document.querySelector('#test');

      draftail.initEditor('#test', {});

      expect(field.draftailEditor.props.ariaDescribedBy).toBe('test-length');
    });

    describe('topToolbar', () => {
      let mockRAF;

      beforeEach(() => {
        jest.useFakeTimers();
        mockRAF = jest
          .spyOn(window, 'requestAnimationFrame')
          .mockImplementation((callback) => callback());
      });

      afterEach(() => {
        mockRAF.mockRestore();
        window.scrollTo.mockClear();
        setWindowScroll({});
        jest.clearAllTimers();
        jest.useRealTimers();
      });

      it('wraps block toolbar actions without changing inline toolbar actions', () => {
        const {
          toolbarProps,
          blockToolbarWrapper,
          blockToolbar,
          inlineToolbar,
        } = getTopToolbarComponents();

        expect(blockToolbarWrapper.props.onMouseDownCapture).toBeDefined();
        expect(blockToolbarWrapper.props.onKeyDownCapture).toBeDefined();
        expect(blockToolbarWrapper.props.onFocusCapture).toBeDefined();
        expect(blockToolbar.props.onCompleteSource).not.toBe(
          toolbarProps.onCompleteSource,
        );
        expect(blockToolbar.props.addHR).not.toBe(toolbarProps.addHR);
        expect(blockToolbar.props.onRequestSource).toBe(
          toolbarProps.onRequestSource,
        );

        expect(inlineToolbar.props.onCompleteSource).toBe(
          toolbarProps.onCompleteSource,
        );
        expect(inlineToolbar.props.addHR).toBe(toolbarProps.addHR);
      });

      it('preserves #main scroll around block type selection', () => {
        const nextState = {};
        const onChange = jest.fn(() => {
          const scrollArea = document.querySelector('#main');
          scrollArea.scrollTop = 0;
          scrollArea.scrollLeft = 0;
        });
        const { blockToolbar } = getTopToolbarComponents(
          { onChange },
          '<main id="main"><input id="test" value="null" /></main>',
        );
        const scrollArea = document.querySelector('#main');
        scrollArea.scrollTop = 600;
        scrollArea.scrollLeft = 40;

        blockToolbar.props.onCompleteSource(nextState);

        expect(onChange).toHaveBeenCalledWith(nextState);
        expect(scrollArea.scrollTop).toBe(600);
        expect(scrollArea.scrollLeft).toBe(40);
      });

      it('preserves document scroll around block type selection', () => {
        const nextState = {};
        const onChange = jest.fn(() => {
          document.documentElement.scrollTop = 0;
          document.documentElement.scrollLeft = 0;
        });
        const { blockToolbar } = getTopToolbarComponents({
          onChange,
        });
        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;

        blockToolbar.props.onCompleteSource(nextState);

        expect(onChange).toHaveBeenCalledWith(nextState);
        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('preserves the scroll captured when opening the block toolbar', () => {
        const nextState = {};
        const onChange = jest.fn(() => {
          document.documentElement.scrollTop = 0;
          document.documentElement.scrollLeft = 0;
        });
        const { blockToolbarWrapper, blockToolbar } = getTopToolbarComponents({
          onChange,
        });
        const trigger = document.createElement('button');
        trigger.className = 'Draftail-BlockToolbar__trigger';

        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;
        blockToolbarWrapper.props.onMouseDownCapture({
          target: trigger,
          preventDefault: jest.fn(),
        });

        document.documentElement.scrollTop = 25;
        document.documentElement.scrollLeft = 5;

        blockToolbar.props.onCompleteSource(nextState);

        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('keeps the opening scroll when combobox focus happens after a jump', () => {
        const nextState = {};
        const onChange = jest.fn(() => {
          document.documentElement.scrollTop = 0;
          document.documentElement.scrollLeft = 0;
        });
        const { blockToolbarWrapper, blockToolbar } = getTopToolbarComponents({
          onChange,
        });
        const trigger = document.createElement('button');
        trigger.className = 'Draftail-BlockToolbar__trigger';
        const input = document.createElement('input');
        input.setAttribute('role', 'combobox');

        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;
        blockToolbarWrapper.props.onMouseDownCapture({
          target: trigger,
          preventDefault: jest.fn(),
        });

        document.documentElement.scrollTop = 0;
        document.documentElement.scrollLeft = 0;
        blockToolbarWrapper.props.onFocusCapture({ target: input });

        document.documentElement.scrollTop = 25;
        document.documentElement.scrollLeft = 5;

        blockToolbar.props.onCompleteSource(nextState);

        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('preserves window scroll around block type selection', () => {
        const nextState = {};
        const onChange = jest.fn();
        const { blockToolbar } = getTopToolbarComponents({
          onChange,
        });
        setWindowScroll({ top: 600, left: 40 });

        blockToolbar.props.onCompleteSource(nextState);

        expect(onChange).toHaveBeenCalledWith(nextState);
        expect(window.scrollTo).toHaveBeenCalledWith(40, 600);
      });

      it('does not call Draftail source completion for block type selection', () => {
        const nextState = {};
        const { toolbarProps, blockToolbar } = getTopToolbarComponents();

        blockToolbar.props.onCompleteSource(nextState);

        expect(toolbarProps.onCompleteSource).not.toHaveBeenCalled();
        expect(toolbarProps.onChange).toHaveBeenCalledWith(nextState);
      });

      it('preserves #main scroll around horizontal rule insertion', () => {
        const addHR = jest.fn(() => {
          const scrollArea = document.querySelector('#main');
          scrollArea.scrollTop = 0;
          scrollArea.scrollLeft = 0;
        });
        const { blockToolbar } = getTopToolbarComponents(
          { addHR },
          '<main id="main"><input id="test" value="null" /></main>',
        );
        const scrollArea = document.querySelector('#main');
        scrollArea.scrollTop = 600;
        scrollArea.scrollLeft = 40;

        blockToolbar.props.addHR();

        expect(addHR).toHaveBeenCalledTimes(1);
        expect(scrollArea.scrollTop).toBe(600);
        expect(scrollArea.scrollLeft).toBe(40);
      });

      it('preserves the scroll captured when opening before horizontal rule insertion', () => {
        const addHR = jest.fn(() => {
          document.documentElement.scrollTop = 0;
          document.documentElement.scrollLeft = 0;
        });
        const { blockToolbarWrapper, blockToolbar } = getTopToolbarComponents({
          addHR,
        });
        const trigger = document.createElement('button');
        trigger.className = 'Draftail-BlockToolbar__trigger';

        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;
        blockToolbarWrapper.props.onMouseDownCapture({
          target: trigger,
          preventDefault: jest.fn(),
        });

        document.documentElement.scrollTop = 25;
        document.documentElement.scrollLeft = 5;

        blockToolbar.props.addHR();

        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('preserves document scroll when opening the block toolbar', () => {
        const { blockToolbarWrapper } = getTopToolbarComponents();
        const trigger = document.createElement('button');
        trigger.className = 'Draftail-BlockToolbar__trigger';
        const preventDefault = jest.fn();
        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;

        blockToolbarWrapper.props.onMouseDownCapture({
          target: trigger,
          preventDefault,
        });

        expect(preventDefault).toHaveBeenCalledTimes(1);
        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('does not preserve scroll for other block toolbar clicks', () => {
        const { blockToolbarWrapper } = getTopToolbarComponents();
        const option = document.createElement('button');
        const preventDefault = jest.fn();
        document.documentElement.scrollTop = 600;

        blockToolbarWrapper.props.onMouseDownCapture({
          target: option,
          preventDefault,
        });

        expect(preventDefault).not.toHaveBeenCalled();
        document.documentElement.scrollTop = 0;
        jest.runOnlyPendingTimers();

        expect(document.documentElement.scrollTop).toBe(0);
      });

      it('preserves scroll when the block toolbar combobox receives focus', () => {
        const { blockToolbarWrapper } = getTopToolbarComponents();
        const input = document.createElement('input');
        input.setAttribute('role', 'combobox');
        document.documentElement.scrollTop = 600;
        document.documentElement.scrollLeft = 40;

        blockToolbarWrapper.props.onFocusCapture({ target: input });

        expect(document.documentElement.scrollTop).toBe(600);
        expect(document.documentElement.scrollLeft).toBe(40);
      });

      it('runs block toolbar actions without #main', () => {
        const nextState = {};
        const onChange = jest.fn();
        const addHR = jest.fn();
        const { blockToolbar } = getTopToolbarComponents({
          onChange,
          addHR,
        });

        expect(() =>
          blockToolbar.props.onCompleteSource(nextState),
        ).not.toThrow();
        expect(() => blockToolbar.props.addHR()).not.toThrow();

        expect(onChange).toHaveBeenCalledWith(nextState);
        expect(addHR).toHaveBeenCalledTimes(1);
      });
    });

    describe('selector conflicts', () => {
      it('fails to instantiate on the right field', () => {
        document.body.innerHTML =
          '<meta name="description" content="null" /><input name="description" value="null" />';

        expect(() => {
          draftail.initEditor('[name="description"]', {}, document.body);
        }).toThrow(SyntaxError);
      });

      it('fails to instantiate on the right field when currentScript is not used', () => {
        window.draftail = draftail;
        document.body.innerHTML = `
          <input name="first" id="description" value="null" />
          <div>
            <input name="last" id="description" value="null" />
            <script data-draftail-script></script>
          </div>
        `;

        draftail.initEditor('#description', {});

        expect(
          document.querySelector('[name="last"]').draftailEditor,
        ).not.toBeDefined();
      });

      it('has no conflict when currentScript is used', () => {
        window.draftail = draftail;
        document.body.innerHTML = `
          <input name="first" id="description" value="null" />
          <div>
            <input name="last" id="description" value="null" />
            <script data-draftail-script></script>
          </div>
        `;

        draftail.initEditor(
          '#description',
          {},
          document.querySelector('[data-draftail-script]'),
        );

        expect(
          document.querySelector('[name="last"]').draftailEditor,
        ).toBeDefined();
      });

      it('uses fallback document.body when currentScript context is wrong', () => {
        window.draftail = draftail;
        document.body.innerHTML = `
        <input id="description" value="null" />
          <div><script data-draftail-script></script></div>
        `;

        draftail.initEditor(
          '#description',
          {},
          document.querySelector('[data-draftail-script]'),
        );

        expect(
          document.querySelector('#description').draftailEditor,
        ).toBeDefined();
      });
    });
  });

  describe('#wrapWagtailIcon', () => {
    it('works', () => {
      expect(wrapWagtailIcon({ icon: 'media' }).icon).toMatchSnapshot();
    });

    it('no icon', () => {
      const type = {};
      expect(wrapWagtailIcon(type)).toBe(type);
    });

    it('array icon', () => {
      const type = { icon: ['M10 10 H 90 V 90 H 10 Z'] };
      expect(wrapWagtailIcon(type)).toBe(type);
    });
  });

  describe('#registerPlugin', () => {
    it('works', () => {
      const plugin = { type: 'TEST' };
      expect(draftail.registerPlugin(plugin, 'entityTypes')).toMatchObject({
        TEST: plugin,
      });
      expect(draftail.registerPlugin(plugin, 'controls')).toMatchObject({
        TEST: plugin,
      });
      expect(draftail.registerPlugin(plugin, 'decorators')).toMatchObject({
        TEST: plugin,
      });
      expect(draftail.registerPlugin(plugin, 'plugins')).toMatchObject({
        TEST: plugin,
      });
    });

    it('supports legacy entityTypes registration', () => {
      const plugin = {
        type: 'TEST_ENTITY',
        source: null,
        decorator: null,
      };

      expect(draftail.registerPlugin(plugin)).toMatchObject({
        TEST_ENTITY: plugin,
      });
    });
  });

  it('#Link', () => expect(Link).toBeDefined());
  it('#Document', () => expect(Document).toBeDefined());
  it('#ImageBlock', () => expect(ImageBlock).toBeDefined());
  it('#EmbedBlock', () => expect(EmbedBlock).toBeDefined());

  it('#ModalWorkflowSource', () =>
    expect(draftail.ModalWorkflowSource).toBeDefined());
  it('#Tooltip', () => expect(draftail.Tooltip).toBeDefined());
  it('#TooltipEntity', () => expect(draftail.TooltipEntity).toBeDefined());
});
