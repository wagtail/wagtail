import draftail, {
  wrapWagtailIcon,
  Link,
  Document,
  ImageBlock,
  EmbedBlock,
} from './index';

window.comments = {
  getContentPath: jest.fn(),
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
