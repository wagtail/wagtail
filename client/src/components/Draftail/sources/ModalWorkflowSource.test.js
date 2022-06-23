import React from 'react';
import { shallow } from 'enzyme';

import { DraftUtils as DraftailUtils } from 'draftail';
import {
  EditorState,
  convertFromRaw,
  AtomicBlockUtils,
  RichUtils,
  Modifier,
} from 'draft-js';
import {
  ImageModalWorkflowSource,
  EmbedModalWorkflowSource,
  LinkModalWorkflowSource,
  DocumentModalWorkflowSource,
} from './ModalWorkflowSource';
import * as DraftUtils from '../DraftUtils';

global.ModalWorkflow = () => {};

describe('ModalWorkflowSource', () => {
  beforeEach(() => {
    jest.spyOn(global, 'ModalWorkflow');
    jest.spyOn(DraftUtils, 'getSelectionText').mockImplementation(() => '');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('works', () => {
    expect(
      shallow(
        <ImageModalWorkflowSource
          editorState={{}}
          entityType={{}}
          entity={null}
          onComplete={() => {}}
          onClose={() => {}}
        />,
      ),
    ).toMatchSnapshot();
  });

  describe('#getChooserConfig', () => {
    const imageSource = new ImageModalWorkflowSource();
    it('IMAGE without entity', () => {
      expect(imageSource.getChooserConfig(null, '')).toEqual({
        url: '/admin/images/chooser/?select_format=true',
        urlParams: {},
        responses: { imageChosen: imageSource.onChosen },
        onload: global.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      });
    });

    it('IMAGE with entity', () => {
      const entity = { getData: () => ({ id: 1, format: 'left', alt: 'alt' }) };
      expect(imageSource.getChooserConfig(entity, '')).toEqual({
        url: '/admin/images/chooser/1/select_format/',
        urlParams: {
          format: 'left',
          alt_text: 'alt',
        },
        responses: { imageChosen: imageSource.onChosen },
        onload: global.IMAGE_CHOOSER_MODAL_ONLOAD_HANDLERS,
      });
    });

    const embedSource = new EmbedModalWorkflowSource();
    it('EMBED without entity', () => {
      expect(embedSource.getChooserConfig(null, '')).toMatchObject({
        url: '/admin/embeds/chooser/',
        urlParams: {},
        onload: global.EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS,
      });
    });

    it('EMBED with entity', () => {
      const entity = { getData: () => ({ url: 'http://example.org/content' }) };
      expect(embedSource.getChooserConfig(entity, '')).toMatchObject({
        url: '/admin/embeds/chooser/',
        urlParams: { url: 'http://example.org/content' },
        onload: global.EMBED_CHOOSER_MODAL_ONLOAD_HANDLERS,
      });
    });

    const documentSource = new DocumentModalWorkflowSource();
    it('DOCUMENT', () => {
      expect(documentSource.getChooserConfig(null, '')).toEqual({
        url: '/admin/documents/chooser/',
        urlParams: {},
        responses: { documentChosen: documentSource.onChosen },
        onload: global.DOCUMENT_CHOOSER_MODAL_ONLOAD_HANDLERS,
      });
    });

    const linkSource = new LinkModalWorkflowSource();
    describe('LINK', () => {
      it('no entity', () => {
        expect(linkSource.getChooserConfig(null, '')).toMatchSnapshot();
      });

      it('page', () => {
        expect(
          linkSource.getChooserConfig(
            {
              getData: () => ({ id: 2, parentId: 1 }),
            },
            '',
          ),
        ).toMatchSnapshot();
      });

      it('root page', () => {
        expect(
          linkSource.getChooserConfig(
            {
              getData: () => ({ id: 1, parentId: null }),
            },
            '',
          ),
        ).toMatchSnapshot();
      });

      it('mail', () => {
        expect(
          linkSource.getChooserConfig(
            {
              getData: () => ({ url: 'mailto:test@example.com' }),
            },
            '',
          ),
        ).toMatchSnapshot();
      });

      it('external', () => {
        expect(
          linkSource.getChooserConfig(
            {
              getData: () => ({ url: 'https://www.example.com/' }),
            },
            '',
          ),
        ).toMatchSnapshot();
      });
    });
  });

  describe('#filterEntityData', () => {
    const imageSource = new ImageModalWorkflowSource();
    it('IMAGE', () => {
      expect(
        imageSource.filterEntityData({
          id: 53,
          title: 'Test',
          alt: 'Test',
          class: 'richtext-image right',
          edit_link: '/admin/images/53/',
          format: 'right',
          preview: {
            url: '/media/images/test.width-500.jpg',
          },
        }),
      ).toMatchSnapshot();
    });

    const embedSource = new EmbedModalWorkflowSource();
    it('EMBED', () => {
      expect(
        embedSource.filterEntityData({
          authorName: 'Test',
          embedType: 'video',
          providerName: 'YouTube',
          thumbnail: 'https://i.ytimg.com/vi/pSlVtxLOYiM/hqdefault.jpg',
          title: 'Test',
          url: 'https://www.youtube.com/watch?v=pSlVtxLOYiM',
        }),
      ).toMatchSnapshot();
    });

    const documentSource = new DocumentModalWorkflowSource();
    it('DOCUMENT', () => {
      expect(
        documentSource.filterEntityData({
          edit_link: '/admin/documents/edit/1/',
          filename: 'test.pdf',
          id: 1,
          title: 'Test',
          url: '/documents/1/test.pdf',
        }),
      ).toMatchSnapshot();
    });

    const linkSource = new LinkModalWorkflowSource();
    describe('LINK', () => {
      it('page', () => {
        expect(
          linkSource.filterEntityData({
            id: 60,
            parentId: 1,
            url: '/',
            editUrl: '/admin/pages/60/edit/',
            title: 'Welcome to the Wagtail Bakery!',
          }),
        ).toMatchSnapshot();
      });

      it('mail', () => {
        expect(
          linkSource.filterEntityData({
            prefer_this_title_as_link_text: false,
            title: 'test@example.com',
            url: 'mailto:test@example.com',
          }),
        ).toMatchSnapshot();
      });

      it('anchor', () => {
        expect(
          linkSource.filterEntityData({
            prefer_this_title_as_link_text: false,
            title: 'testanchor',
            url: '#testanchor',
          }),
        ).toMatchSnapshot();
      });

      it('external', () => {
        expect(
          linkSource.filterEntityData({
            prefer_this_title_as_link_text: false,
            title: 'https://www.example.com/',
            url: 'https://www.example.com/',
          }),
        ).toMatchSnapshot();
      });
    });
  });

  it('#componentDidMount', () => {
    const wrapper = shallow(
      <EmbedModalWorkflowSource
        editorState={EditorState.createEmpty()}
        entityType={{}}
        entity={null}
        onComplete={() => {}}
        onClose={() => {}}
      />,
    );

    wrapper.instance().onChosen = jest.fn();

    wrapper.instance().componentDidMount();

    global.ModalWorkflow.mock.calls[0][0].responses.embedChosen('test', {});

    expect(global.ModalWorkflow).toHaveBeenCalled();
    expect(global.jQuery().on).toHaveBeenCalled();
    expect(wrapper.instance().onChosen).toHaveBeenCalled();
  });

  it('#onError', () => {
    window.alert = jest.fn();
    const onClose = jest.fn();

    const wrapper = shallow(
      <EmbedModalWorkflowSource
        editorState={EditorState.createEmpty()}
        entityType={{}}
        entity={null}
        onComplete={() => {}}
        onClose={onClose}
      />,
    );

    wrapper.instance().componentDidMount();

    global.ModalWorkflow.mock.calls[0][0].onError();

    expect(global.ModalWorkflow).toHaveBeenCalled();
    expect(global.jQuery().on).toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it('#componentWillUnmount', () => {
    const wrapper = shallow(
      <EmbedModalWorkflowSource
        editorState={EditorState.createEmpty()}
        entityType={{}}
        entity={null}
        onComplete={() => {}}
        onClose={() => {}}
      />,
    );

    wrapper.instance().componentWillUnmount();

    expect(global.jQuery().off).toHaveBeenCalled();
  });

  describe('#onChosen', () => {
    it('works', () => {
      jest.spyOn(RichUtils, 'toggleLink');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(
        convertFromRaw({
          entityMap: {},
          blocks: [
            {
              key: 'a',
              text: 'test',
            },
          ],
        }),
      );
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow(
        <LinkModalWorkflowSource
          editorState={editorState}
          entityType={{}}
          entity={null}
          onComplete={onComplete}
          onClose={() => {}}
        />,
      );

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({});

      expect(onComplete).toHaveBeenCalled();
      expect(RichUtils.toggleLink).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      RichUtils.toggleLink.mockRestore();
    });

    it('block for new entity', () => {
      jest.spyOn(AtomicBlockUtils, 'insertAtomicBlock');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(
        convertFromRaw({
          entityMap: {},
          blocks: [
            {
              key: 'a',
              text: 'test',
            },
          ],
        }),
      );
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow(
        <LinkModalWorkflowSource
          editorState={editorState}
          entityType={{
            block: () => {},
          }}
          entity={null}
          onComplete={onComplete}
          onClose={() => {}}
        />,
      );

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({});

      expect(onComplete).toHaveBeenCalled();
      expect(AtomicBlockUtils.insertAtomicBlock).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      AtomicBlockUtils.insertAtomicBlock.mockRestore();
    });

    it('block for existing entity', () => {
      jest.spyOn(DraftailUtils, 'updateBlockEntity');
      const onComplete = jest.fn();
      const close = jest.fn();
      const entity = { getData: () => ({ id: 1, format: 'left', alt: 'alt' }) };

      let editorState = EditorState.createWithContent(
        convertFromRaw({
          blocks: [
            {
              key: 'a',
              text: ' ',
              type: 'atomic',
              entityRanges: [{ offset: 0, length: 1, key: 'first' }],
              data: {},
            },
          ],
          entityMap: {
            first: {
              type: 'IMAGE',
              mutability: 'IMMUTABLE',
              data: {},
            },
          },
        }),
      );
      let selection = editorState.getSelection();
      selection = selection.merge({
        anchorKey: 'a',
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow(
        <ImageModalWorkflowSource
          editorState={editorState}
          entityType={{
            block: () => {},
          }}
          entity={entity}
          entityKey="first"
          onComplete={onComplete}
          onClose={() => {}}
        />,
      );

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({
        id: 2,
        preview: { url: '/foo' },
        alt: 'new image',
        format: 'left',
      });

      expect(onComplete).toHaveBeenCalled();
      expect(DraftailUtils.updateBlockEntity).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      DraftailUtils.updateBlockEntity.mockRestore();
    });

    it('prefer_this_title_as_link_text', () => {
      jest.spyOn(Modifier, 'replaceText');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(
        convertFromRaw({
          entityMap: {},
          blocks: [
            {
              key: 'a',
              text: 'test',
            },
          ],
        }),
      );
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow(
        <LinkModalWorkflowSource
          editorState={editorState}
          entityType={{}}
          onComplete={onComplete}
          onClose={() => {}}
        />,
      );

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({
        url: 'example.com',
        prefer_this_title_as_link_text: true,
      });

      expect(onComplete).toHaveBeenCalled();
      expect(Modifier.replaceText).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      Modifier.replaceText.mockRestore();
    });
  });

  it('#onClose', () => {
    const onClose = jest.fn();
    const wrapper = shallow(
      <LinkModalWorkflowSource
        editorState={EditorState.createEmpty()}
        entityType={{}}
        entity={null}
        onComplete={() => {}}
        onClose={onClose}
      />,
    );

    wrapper.instance().onClose({
      preventDefault: () => {},
    });

    expect(onClose).toHaveBeenCalled();
  });
});
