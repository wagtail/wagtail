import { shallow } from 'enzyme';
import React from 'react';

import PageExplorerItem from './PageExplorerItem';

const getMockProps = (meta = {}) => ({
  item: {
    id: 5,
    admin_display_title: 'test',
    meta: {
      depth: 3,
      status: 'live',
      live: true,
      has_unpublished_changes: false,
      has_children: false,
      locale: 'en',
      ...meta,
    },
  },
  onClick: () => {},
});

describe('PageExplorerItem', () => {
  it('exists', () => {
    expect(PageExplorerItem).toBeDefined();
  });

  it('renders', () => {
    expect(shallow(<PageExplorerItem {...getMockProps()} />)).toMatchSnapshot();
  });

  it('children', () => {
    const wrapper = shallow(
      <PageExplorerItem {...getMockProps({ has_children: true })} />,
    );
    expect(wrapper.find('Icon[name="folder-inverse"]')).toHaveLength(1);
    expect(wrapper.find('Icon[name="arrow-right"]')).toHaveLength(1);
    expect(wrapper).toMatchSnapshot();
  });

  it('should show a publication status with unpublished changes', () => {
    const wrapper = shallow(
      <PageExplorerItem
        {...getMockProps({
          status: 'live + draft',
          has_unpublished_changes: true,
        })}
      />,
    );
    expect(wrapper.find('PublicationStatus').prop('status')).toEqual({
      status: 'live + draft',
      live: true,
    });
    expect(wrapper).toMatchSnapshot();
  });

  it('should show a publication status if not live', () => {
    const wrapper = shallow(
      <PageExplorerItem
        {...getMockProps({
          status: 'draft',
          live: false,
          has_unpublished_changes: true,
        })}
      />,
    );
    expect(wrapper.find('PublicationStatus').prop('status')).toEqual({
      status: 'draft',
      live: false,
    });
    expect(wrapper).toMatchSnapshot();
  });

  it('should not show a publication status if live without changes', () => {
    const wrapper = shallow(<PageExplorerItem {...getMockProps()} />);
    expect(wrapper.find('PublicationStatus')).toHaveLength(0);
  });

  it('should show the locale for top-level pages', () => {
    const wrapper = shallow(
      <PageExplorerItem {...getMockProps({ depth: 2, locale: 'fr' })} />,
    );
    expect(wrapper.find('.c-page-explorer__meta .c-status').text()).toBe(
      'French',
    );
  });

  it('should not show the locale for deeper pages', () => {
    const wrapper = shallow(
      <PageExplorerItem {...getMockProps({ depth: 3, locale: 'fr' })} />,
    );
    expect(wrapper.find('.c-page-explorer__meta')).toHaveLength(0);
  });
});
