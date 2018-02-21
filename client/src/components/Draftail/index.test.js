import draftail, {
  wrapWagtailIcon,
  ModalWorkflowSource,
  Link,
  Document,
  ImageBlock,
  EmbedBlock,
} from './index';

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

      draftail.registerPlugin({
        type: 'IMAGE',
        source: () => {},
        block: () => {},
      });

      draftail.initEditor('#test', {
        entityTypes: [
          { type: 'IMAGE' },
        ],
        enableHorizontalRule: true,
      });

      expect(field.draftailEditor.props).toMatchSnapshot();
    });

    describe('selector conflicts', () => {
      it('fails to instantiate on the right field', () => {
        document.body.innerHTML = '<meta name="description" content="null" /><input name="description" value="null" />';

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
            <script>window.draftail.initEditor('#description', {});</script>
          </div>
        `;

        expect(document.querySelector('[name="last"]').draftailEditor).not.toBeDefined();
      });

      it('has no conflict when currentScript is used', () => {
        window.draftail = draftail;
        document.body.innerHTML = `
          <input name="first" id="description" value="null" />
          <div>
            <input name="last" id="description" value="null" />
            <script>window.draftail.initEditor('#description', {}, document.currentScript);</script>
          </div>
        `;

        expect(document.querySelector('[name="last"]').draftailEditor).toBeDefined();
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
      const plugin = {
        type: 'TEST',
        source: null,
        decorator: null,
      };

      expect(draftail.registerPlugin(plugin)).toMatchObject({
        TEST: plugin,
      });
    });
  });

  it('#ModalWorkflowSource', () => expect(ModalWorkflowSource).toBeDefined());
  it('#Link', () => expect(Link).toBeDefined());
  it('#Document', () => expect(Document).toBeDefined());
  it('#ImageBlock', () => expect(ImageBlock).toBeDefined());
  it('#EmbedBlock', () => expect(EmbedBlock).toBeDefined());
});
