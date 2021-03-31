import { basicCommentsState } from '../__fixtures__/state';
import { INITIAL_STATE } from '../state/settings';

import { selectCommentsForContentPathFactory } from './index';

test('Select comments for contentpath', () => {
  // test that the selectCommentsForContentPathFactory can generate selectors for the two contentpaths in basicCommentsState
  const state = {
    comments: basicCommentsState,
    settings: INITIAL_STATE,
  };
  const testContentPathSelector = selectCommentsForContentPathFactory(
    'test_contentpath'
  );
  const testContentPathSelector2 = selectCommentsForContentPathFactory(
    'test_contentpath_2'
  );
  const selectedComments = testContentPathSelector(state);
  expect(selectedComments.length).toBe(1);
  expect(selectedComments[0].contentpath).toBe('test_contentpath');
  const otherSelectedComments = testContentPathSelector2(state);
  expect(otherSelectedComments.length).toBe(1);
  expect(otherSelectedComments[0].contentpath).toBe('test_contentpath_2');
});
