import { basicCommentsState } from '../__fixtures__/state';
import { INITIAL_STATE as INITIAL_SETTINGS_STATE } from '../state/settings';
import {
  INITIAL_STATE as INITIAL_COMMENTS_STATE,
  newComment,
  newCommentReply,
} from '../state/comments';
import { reducer } from '../state';

import * as actions from '../actions/comments';

import { selectCommentsForContentPathFactory, selectIsDirty } from './index';

test('Select comments for contentpath', () => {
  // test that the selectCommentsForContentPathFactory can generate selectors for the two
  // contentpaths in basicCommentsState
  const state = {
    comments: basicCommentsState,
    settings: INITIAL_SETTINGS_STATE,
  };
  const testContentPathSelector =
    selectCommentsForContentPathFactory('test_contentpath');
  const testContentPathSelector2 =
    selectCommentsForContentPathFactory('test_contentpath_2');
  const selectedComments = testContentPathSelector(state);
  expect(selectedComments.length).toBe(1);
  expect(selectedComments[0].contentpath).toBe('test_contentpath');
  const otherSelectedComments = testContentPathSelector2(state);
  expect(otherSelectedComments.length).toBe(1);
  expect(otherSelectedComments[0].contentpath).toBe('test_contentpath_2');
});

test('Select is dirty', () => {
  const state = {
    comments: INITIAL_COMMENTS_STATE,
    settings: INITIAL_SETTINGS_STATE,
  };
  const stateWithUnsavedComment = reducer(
    state,
    actions.addComment(
      newComment('test_contentpath', 'test_position', 1, null, null, 0, {
        remoteId: null,
        text: 'my new comment',
      }),
    ),
  );

  expect(selectIsDirty(stateWithUnsavedComment)).toBe(true);

  const stateWithSavedComment = reducer(
    state,
    actions.addComment(
      newComment('test_contentpath', 'test_position', 1, null, null, 0, {
        remoteId: 1,
        text: 'my saved comment',
      }),
    ),
  );

  expect(selectIsDirty(stateWithSavedComment)).toBe(false);

  const stateWithDeletedComment = reducer(
    stateWithSavedComment,
    actions.deleteComment(1),
  );

  expect(selectIsDirty(stateWithDeletedComment)).toBe(true);

  const stateWithResolvedComment = reducer(
    stateWithSavedComment,
    actions.updateComment(1, { resolved: true }),
  );

  expect(selectIsDirty(stateWithResolvedComment)).toBe(true);

  const stateWithEditedComment = reducer(
    stateWithSavedComment,
    actions.updateComment(1, { text: 'edited_text' }),
  );

  expect(selectIsDirty(stateWithEditedComment)).toBe(true);

  const stateWithUnsavedReply = reducer(
    stateWithSavedComment,
    actions.addReply(
      1,
      newCommentReply(2, null, 0, {
        remoteId: null,
        text: 'new reply',
      }),
    ),
  );

  expect(selectIsDirty(stateWithUnsavedReply)).toBe(true);

  const stateWithSavedReply = reducer(
    stateWithSavedComment,
    actions.addReply(
      1,
      newCommentReply(2, null, 0, {
        remoteId: 2,
        text: 'new saved reply',
      }),
    ),
  );

  expect(selectIsDirty(stateWithSavedReply)).toBe(false);

  const stateWithDeletedReply = reducer(
    stateWithSavedReply,
    actions.deleteReply(1, 2),
  );

  expect(selectIsDirty(stateWithDeletedReply)).toBe(true);

  const stateWithEditedReply = reducer(
    stateWithSavedReply,
    actions.updateReply(1, 2, { text: 'edited_text' }),
  );

  expect(selectIsDirty(stateWithEditedReply)).toBe(true);
});
