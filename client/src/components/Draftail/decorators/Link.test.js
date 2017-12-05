import React from 'react';
import { shallow } from 'enzyme';
import { convertFromHTML, ContentState } from 'draft-js';
import Link from './Link';

describe('Link', () => {
  it('exists', () => {
    expect(Link).toBeDefined();
  });

  it('renders', () => {
    const contentBlocks = convertFromHTML('<h1>aaaaaaaaaa</h1>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    const contentStateWithEntity = contentState.createEntity('LINK', 'MUTABLE', { url: 'http://example.com/' });
    const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
    expect(shallow((
      <Link
        entityKey={entityKey}
        contentState={contentStateWithEntity}
      >
        <span>Test children</span>
      </Link>
    ))).toMatchSnapshot();
  });

  it('renders email', () => {
    const contentBlocks = convertFromHTML('<h1>aaaaaaaaaa</h1>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    const contentStateWithEntity = contentState.createEntity('LINK', 'MUTABLE', { url: 'mailto:test@example.com' });
    const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
    expect(shallow((
      <Link
        entityKey={entityKey}
        contentState={contentStateWithEntity}
      >
        <span>Test children</span>
      </Link>
    ))).toMatchSnapshot();
  });
});
