import React from 'react';
import { shallow } from 'enzyme';
import { convertFromHTML, ContentState } from 'draft-js';
import Document from './Document';

describe('Document', () => {
  it('exists', () => {
    expect(Document).toBeDefined();
  });

  it('renders', () => {
    const contentBlocks = convertFromHTML('<h1>aaaaaaaaaa</h1>');
    const contentState = ContentState.createFromBlockArray(contentBlocks);
    const contentStateWithEntity = contentState.createEntity('DOCUMENT', 'MUTABLE', { title: 'Test title' });
    const entityKey = contentStateWithEntity.getLastCreatedEntityKey();
    expect(shallow((
      <Document
        entityKey={entityKey}
        contentState={contentStateWithEntity}
      >
        <span>Test children</span>
      </Document>
    ))).toMatchSnapshot();
  });
});
