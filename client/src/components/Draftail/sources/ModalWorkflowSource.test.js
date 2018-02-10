import React from 'react';
import { shallow } from 'enzyme';

import ModalWorkflowSource, { getChooserConfig, filterEntityData } from './ModalWorkflowSource';
import { EditorState, convertFromRaw, AtomicBlockUtils, RichUtils, Modifier } from 'draft-js';

global.ModalWorkflow = () => {};

describe('ModalWorkflowSource', () => {
  beforeEach(() => {
    jest.spyOn(global, 'ModalWorkflow');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('works', () => {
    expect(shallow((
      <ModalWorkflowSource
        editorState={{}}
        entityType={{}}
        entity={{}}
        onComplete={() => {}}
        onClose={() => {}}
      />
    ))).toMatchSnapshot();
  });

  describe('#getChooserConfig', () => {
    it('IMAGE', () => {
      expect(getChooserConfig({ type: 'IMAGE' })).toEqual({
        url: '/admin/images/chooser/?select_format=true',
        urlParams: {},
      });
    });

    it('EMBED', () => {
      expect(getChooserConfig({ type: 'EMBED' })).toEqual({
        url: '/admin/embeds/chooser/',
        urlParams: {},
      });
    });

    it('DOCUMENT', () => {
      expect(getChooserConfig({ type: 'DOCUMENT' })).toEqual({
        url: '/admin/documents/chooser/',
        urlParams: {},
      });
    });

    describe('LINK', () => {
      it('no entity', () => {
        expect(getChooserConfig({ type: 'LINK' })).toMatchSnapshot();
      });

      it('page', () => {
        expect(getChooserConfig({ type: 'LINK' }, {
          getData: () => ({ id: 1, parentId: 0 })
        })).toMatchSnapshot();
      });

      it('mail', () => {
        expect(getChooserConfig({ type: 'LINK' }, {
          getData: () => ({ url: 'mailto:test@example.com' })
        })).toMatchSnapshot();
      });

      it('external', () => {
        expect(getChooserConfig({ type: 'LINK' }, {
          getData: () => ({ url: 'https://www.example.com/' })
        })).toMatchSnapshot();
      });
    });
  });

  describe('#filterEntityData', () => {
    it('IMAGE', () => {
      expect(filterEntityData({ type: 'IMAGE' }, {
        id: 53,
        title: 'Test',
        alt: 'Test',
        class: 'richtext-image right',
        edit_link: '/admin/images/53/',
        format: 'right',
        preview: {
          url: '/media/images/test.width-500.jpg',
        }
      })).toMatchSnapshot();
    });

    it('EMBED', () => {
      expect(filterEntityData({ type: 'EMBED' }, {
        authorName: 'Test',
        embedType: 'video',
        providerName: 'YouTube',
        thumbnail: 'https://i.ytimg.com/vi/pSlVtxLOYiM/hqdefault.jpg',
        title: 'Test',
        url: 'https://www.youtube.com/watch?v=pSlVtxLOYiM',
      })).toMatchSnapshot();
    });

    it('DOCUMENT', () => {
      expect(filterEntityData({ type: 'DOCUMENT' }, {
        edit_link: '/admin/documents/edit/1/',
        filename: 'test.pdf',
        id: 1,
        title: 'Test',
        url: '/documents/1/test.pdf',
      })).toMatchSnapshot();
    });

    it('OTHER', () => {
      expect(filterEntityData({ type: 'OTHER' }, {})).toEqual({});
    });

    describe('LINK', () => {
      it('page', () => {
        expect(filterEntityData({ type: 'LINK' }, {
          id: 60,
          parentId: 1,
          url: '/',
          editUrl: '/admin/pages/60/edit/',
          title: 'Welcome to the Wagtail Bakery!',
        })).toMatchSnapshot();
      });

      it('mail', () => {
        expect(filterEntityData({ type: 'LINK' }, {
          prefer_this_title_as_link_text: false,
          title: 'test@example.com',
          url: 'mailto:test@example.com',
        })).toMatchSnapshot();
      });

      it('external', () => {
        expect(filterEntityData({ type: 'LINK' }, {
          prefer_this_title_as_link_text: false,
          title: 'https://www.example.com/',
          url: 'https://www.example.com/',
        })).toMatchSnapshot();
      });
    });
  });

  it('#componentDidMount', () => {
    const wrapper = shallow((
      <ModalWorkflowSource
        editorState={{}}
        entityType={{}}
        entity={{}}
        onComplete={() => {}}
        onClose={() => {}}
      />
    ));

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

    const wrapper = shallow((
      <ModalWorkflowSource
        editorState={{}}
        entityType={{}}
        entity={{}}
        onComplete={() => {}}
        onClose={onClose}
      />
    ));

    wrapper.instance().componentDidMount();

    global.ModalWorkflow.mock.calls[0][0].onError();

    expect(global.ModalWorkflow).toHaveBeenCalled();
    expect(global.jQuery().on).toHaveBeenCalled();
    expect(window.alert).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalled();
  });

  it('#componentWillUnmount', () => {
    const wrapper = shallow((
      <ModalWorkflowSource
        editorState={{}}
        entityType={{}}
        entity={{}}
        onComplete={() => {}}
        onClose={() => {}}
      />
    ));

    wrapper.instance().componentWillUnmount();

    expect(global.jQuery().off).toHaveBeenCalled();
  });

  describe('#onChosen', () => {
    it('works', () => {
      jest.spyOn(RichUtils, 'toggleLink');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test',
          }
        ]
      }));
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow((
        <ModalWorkflowSource
          editorState={editorState}
          entityType={{}}
          entity={{}}
          onComplete={onComplete}
          onClose={() => {}}
        />
      ));

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({});

      expect(onComplete).toHaveBeenCalled();
      expect(RichUtils.toggleLink).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      RichUtils.toggleLink.mockRestore();
    });

    it('block', () => {
      jest.spyOn(AtomicBlockUtils, 'insertAtomicBlock');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test',
          }
        ]
      }));
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow((
        <ModalWorkflowSource
          editorState={editorState}
          entityType={{
            block: () => {},
          }}
          entity={{}}
          onComplete={onComplete}
          onClose={() => {}}
        />
      ));

      wrapper.instance().workflow = { close };
      wrapper.instance().onChosen({});

      expect(onComplete).toHaveBeenCalled();
      expect(AtomicBlockUtils.insertAtomicBlock).toHaveBeenCalled();
      expect(close).toHaveBeenCalled();

      AtomicBlockUtils.insertAtomicBlock.mockRestore();
    });

    it('prefer_this_title_as_link_text', () => {
      jest.spyOn(Modifier, 'replaceText');

      const onComplete = jest.fn();
      const close = jest.fn();

      let editorState = EditorState.createWithContent(convertFromRaw({
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test',
          }
        ]
      }));
      let selection = editorState.getSelection();
      selection = selection.merge({
        focusOffset: 4,
      });
      editorState = EditorState.acceptSelection(editorState, selection);
      const wrapper = shallow((
        <ModalWorkflowSource
          editorState={editorState}
          entityType={{}}
          onComplete={onComplete}
          onClose={() => {}}
        />
      ));

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
    const wrapper = shallow((
      <ModalWorkflowSource
        editorState={{}}
        entityType={{}}
        entity={{}}
        onComplete={() => {}}
        onClose={onClose}
      />
    ));

    wrapper.instance().onClose({
      preventDefault: () => {},
    });

    expect(onClose).toHaveBeenCalled();
  });
});
