import React from 'react';
import { shallow } from 'enzyme';

import PageExplorerItem from './PageExplorerItem';

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
      },
    },
  },
  onClick: () => {},
};

describe('PageExplorerItem', () => {
  it('exists', () => {
    expect(PageExplorerItem).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<PageExplorerItem {...mockProps} />)).toMatchSnapshot();
  });

  it('children', () => {
    const props = { ...mockProps };
    props.item.meta.children.count = 5;
    expect(shallow(<PageExplorerItem {...props} />)).toMatchSnapshot();
  });

  it('should show a publication status with unpublished changes', () => {
    const props = { ...mockProps };
    props.item.meta.status.has_unpublished_changes = true;
    expect(shallow(<PageExplorerItem {...props} />)).toMatchSnapshot();
  });

  it('should show a publication status if not live', () => {
    const props = { ...mockProps };
    props.item.meta.status.live = false;
    expect(shallow(<PageExplorerItem {...props} />)).toMatchSnapshot();
  });
});
