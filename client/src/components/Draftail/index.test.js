import {
  wrapWagtailIcon,
  initEditor,
  registry,
  ModalWorkflowSource,
  Link,
  Document,
  ImageBlock,
  EmbedBlock,
} from './index';

describe('Draftail', () => {
  describe('#initEditor', () => {
    beforeEach(() => {
      document.body.innerHTML = '';
    });

    it('works', () => {
      const field = document.createElement('input');
      field.name = 'test';
      field.value = 'null';
      document.body.appendChild(field);

      initEditor('test', {});

      expect(field.draftailEditor).toBeDefined();
    });

    it('onSave', () => {
      const field = document.createElement('input');
      field.name = 'test';
      field.value = 'null';
      document.body.appendChild(field);

      initEditor('test', {});

      field.draftailEditor.saveState();

      expect(field.value).toBe('null');
    });

    it('options', () => {
      const field = document.createElement('input');
      field.name = 'test';
      field.value = 'null';
      document.body.appendChild(field);

      registry.registerPlugin({
        type: 'IMAGE',
        source: () => {},
        block: () => {},
      });

      initEditor('test', {
        entityTypes: [
          { type: 'IMAGE' },
        ],
        enableHorizontalRule: true,
      });

      expect(field.draftailEditor.props).toMatchSnapshot();
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

  it('#registry', () => expect(registry).toBeDefined());
  it('#ModalWorkflowSource', () => expect(ModalWorkflowSource).toBeDefined());
  it('#Link', () => expect(Link).toBeDefined());
  it('#Document', () => expect(Document).toBeDefined());
  it('#ImageBlock', () => expect(ImageBlock).toBeDefined());
  it('#EmbedBlock', () => expect(EmbedBlock).toBeDefined());
});
