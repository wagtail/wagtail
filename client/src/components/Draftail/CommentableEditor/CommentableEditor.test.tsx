import React, { ReactNode } from 'react';
import { Provider } from 'react-redux';
import { mount } from 'enzyme';
import { createEditorStateFromRaw } from 'draftail';

import { CommentApp } from '../../CommentApp/main';
import { updateGlobalSettings } from '../../CommentApp/actions/settings';
import { newComment } from '../../CommentApp/state/comments';

import CommentableEditor, {
  updateCommentPositions,
  addCommentsToEditor,
  DraftailInlineAnnotation,
  findLeastCommonCommentId,
} from './CommentableEditor';

describe('CommentableEditor', () => {
  const content = {
    entityMap: {},
    blocks: [
      {
        key: 'a',
        type: 'unstyled',
        depth: 0,
        inlineStyleRanges: [],
        text: 'test',
        entityRanges: [],
      },
    ],
  };
  const contentWithComment = {
    entityMap: {},
    blocks: [
      {
        key: 'a',
        type: 'unstyled',
        depth: 0,
        inlineStyleRanges: [
          {
            offset: 0,
            length: 1,
            style: 'COMMENT-1',
          },
        ],
        text: 'test',
        entityRanges: [],
      },
    ],
  };
  const contentWithOverlappingComments = {
    entityMap: {},
    blocks: [
      {
        key: 'a',
        type: 'unstyled',
        depth: 0,
        inlineStyleRanges: [
          {
            offset: 0,
            length: 10,
            style: 'COMMENT-2',
          },
          {
            offset: 0,
            length: 20,
            style: 'COMMENT-1',
          },
        ],
        text: 'test_test_test_test_test_test_test',
        entityRanges: [],
      },
    ],
  };
  let commentApp: CommentApp;
  let fieldNode: HTMLElement;
  let getEditorComponent: (app: CommentApp) => ReactNode;
  const contentpath = 'test-contentpath';
  const getComments = (app: CommentApp) =>
    app.utils.selectCommentsForContentPathFactory(contentpath)(
      app.store.getState()
    );
  beforeAll(() => {
    const commentsElement = document.createElement('div');
    document.body.appendChild(commentsElement);
    const commentsOutputElement = document.createElement('div');
    document.body.appendChild(commentsOutputElement);
    fieldNode = document.createElement('div');
    document.body.appendChild(fieldNode);
    getEditorComponent = (app) => (
      <Provider store={app.store}>
        <CommentableEditor
          commentApp={app}
          fieldNode={fieldNode}
          contentPath={contentpath}
          rawContentState={content}
          onSave={() => {}}
          inlineStyles={[]}
          editorRef={() => {}}
          colorConfig={{
            standardHighlight: '#FF0000',
            overlappingHighlight: '#00FF00',
            focusedHighlight: '#000000',
          }}
          isCommentShortcut={() => false}
        />
      </Provider>
    );
  });
  beforeEach(() => {
    commentApp = new CommentApp();
  });
  it('has control', () => {
    commentApp.setVisible(true);
    const editor = mount(getEditorComponent(commentApp));
    const controls = editor.findWhere(
      (n) => n.name() === 'ToolbarButton' && n.prop('name') === 'comment'
    );
    expect(controls).toHaveLength(1);
    editor.unmount();
  });
  it('has no control when comments disabled', () => {
    commentApp.store.dispatch(updateGlobalSettings({ commentsEnabled: false }));
    const editor = mount(getEditorComponent(commentApp));
    const controls = editor.findWhere(
      (n) => n.name() === 'ToolbarButton' && n.prop('name') === 'comment'
    );
    expect(controls).toHaveLength(0);
    editor.unmount();
  });
  it('can update comment positions', () => {
    commentApp.store.dispatch(
      commentApp.actions.addComment(
        newComment('test-contentpath', 'old_position', 1, null, null, 0, {})
      )
    );
    // Test that a comment with no annotation will not have its position updated
    updateCommentPositions({
      editorState: createEditorStateFromRaw(content),
      comments: getComments(commentApp),
      commentApp: commentApp,
    });
    expect(commentApp.store.getState().comments.comments.get(1)?.position).toBe(
      'old_position'
    );

    commentApp.updateAnnotation(new DraftailInlineAnnotation(fieldNode), 1);

    // Test that a comment with no style in the ContentState will have an empty position set
    updateCommentPositions({
      editorState: createEditorStateFromRaw(content),
      comments: getComments(commentApp),
      commentApp: commentApp,
    });
    expect(commentApp.store.getState().comments.comments.get(1)?.position).toBe(
      '[]'
    );

    // Test that a comment with a style range has that style range recorded accurately in the state
    updateCommentPositions({
      editorState: createEditorStateFromRaw(contentWithComment),
      comments: getComments(commentApp),
      commentApp: commentApp,
    });
    expect(commentApp.store.getState().comments.comments.get(1)?.position).toBe(
      '[{"key":"a","start":0,"end":1}]'
    );
  });
  it('can add comments to editor', () => {
    commentApp.store.dispatch(
      commentApp.actions.addComment(
        newComment(
          contentpath,
          '[{"key":"a","start":0,"end":1}]',
          1,
          null,
          null,
          0,
          {}
        )
      )
    );
    // Test that comment styles are correctly added to the editor,
    // and the comments in the state have annotations assigned
    const newContentState = addCommentsToEditor(
      createEditorStateFromRaw(content).getCurrentContent(),
      getComments(commentApp),
      commentApp,
      () => new DraftailInlineAnnotation(fieldNode)
    );
    newContentState.getFirstBlock().findStyleRanges(
      (metadata) => !metadata.getStyle().isEmpty(),
      (start, end) => {
        expect(
          newContentState
            .getFirstBlock()
            .getInlineStyleAt(start)
            .has('COMMENT-1')
        ).toBe(true);
        expect(start).toBe(0);
        expect(end).toBe(1);
      }
    );
    expect(
      commentApp.store.getState().comments.comments.get(1)?.annotation
    ).not.toBe(null);
  });
  it('can find the least common comment id', () => {
    const block = createEditorStateFromRaw(contentWithOverlappingComments)
      .getCurrentContent()
      .getFirstBlock();

    // In the overlapping range, comment 2 covers the least, so should be found
    expect(findLeastCommonCommentId(block, 0)).toBe(2);

    // In the non overlapping range, only comment 1 exists, so should be found
    expect(findLeastCommonCommentId(block, 11)).toBe(1);
  });
});
