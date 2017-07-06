import React from 'react';
import { shallow } from 'enzyme';

import ExplorerItem from './ExplorerItem';

const mockProps = {
  item: {
    id: 5,
    admin_display_title: 'test',
    meta: {
      latest_revision_created_at: null,
      status: {
        live: true,
        status: 'test',
        has_unpublished_changes: false,
      },
      descendants: {
        count: 0,
      },
      children: {
        count: 0,
      }
    },
  },
  onClick: () => {},
};

describe('ExplorerItem', () => {
  it('exists', () => {
    expect(ExplorerItem).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<ExplorerItem {...mockProps} />)).toMatchSnapshot();
  });

  it('children', () => {
    const props = Object.assign({}, mockProps);
    props.item.meta.children.count = 5;
    expect(shallow(<ExplorerItem {...props} />)).toMatchSnapshot();
  });

  it('should show a publication status with unpublished changes', () => {
    const props = Object.assign({}, mockProps);
    props.item.meta.status.has_unpublished_changes = true;
    expect(shallow(<ExplorerItem {...props} />)).toMatchSnapshot();
  });

  it('should show a publication status if not live', () => {
    const props = Object.assign({}, mockProps);
    props.item.meta.status.live = false;
    expect(shallow(<ExplorerItem {...props} />)).toMatchSnapshot();
  });
});
