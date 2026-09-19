import { shallow } from 'enzyme';
import React from 'react';
import PageExplorerPanel from './PageExplorerPanel';

const mockProps = {
  page: {
    children: {
      items: [],
    },
    meta: {
      parent: null,
    },
  },
  depth: 1,
  onClose: jest.fn(),
  gotoPage: jest.fn(),
  nodes: {},
};

describe('PageExplorerPanel', () => {
  describe('general rendering', () => {
    beforeEach(() => {
      document.body.innerHTML = '<div></div>';
    });

    it('exists', () => {
      expect(PageExplorerPanel).toBeDefined();
    });

    it('renders', () => {
      expect(shallow(<PageExplorerPanel {...mockProps} />)).toMatchSnapshot();
    });

    it('#isFetching', () => {
      expect(
        shallow(
          <PageExplorerPanel
            {...mockProps}
            page={{ isFetching: true, ...mockProps.page }}
          />,
        ),
      ).toMatchSnapshot();
    });

    it('#isError', () => {
      expect(
        shallow(
          <PageExplorerPanel
            {...mockProps}
            page={{ isError: true, ...mockProps.page }}
          />,
        ),
      ).toMatchSnapshot();
    });

    it('no children', () => {
      expect(
        shallow(<PageExplorerPanel {...mockProps} page={{ children: {} }} />),
      ).toMatchSnapshot();
    });

    it('#items', () => {
      expect(
        shallow(
          <PageExplorerPanel
            {...mockProps}
            page={{ children: { items: [1, 2] } }}
            nodes={{
              1: {
                id: 1,
                admin_display_title: 'Test',
                meta: { status: {}, type: 'test' },
              },
              2: {
                id: 2,
                admin_display_title: 'Foo',
                meta: { status: {}, type: 'foo' },
              },
            }}
          />,
        ),
      ).toMatchSnapshot();
    });
  });

  describe('onHeaderClick', () => {
    beforeEach(() => {
      mockProps.gotoPage.mockReset();
    });

    it('calls gotoPage', () => {
      shallow(
        <PageExplorerPanel
          {...mockProps}
          depth={2}
          page={{ children: { items: [] }, meta: { parent: { id: 1 } } }}
        />,
      )
        .find('PageExplorerHeader')
        .prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).toHaveBeenCalled();
    });

    it('does not call gotoPage for first page', () => {
      shallow(
        <PageExplorerPanel
          {...mockProps}
          depth={0}
          page={{ children: { items: [] }, meta: { parent: { id: 1 } } }}
        />,
      )
        .find('PageExplorerHeader')
        .prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).not.toHaveBeenCalled();
    });
  });

  describe('onItemClick', () => {
    beforeEach(() => {
      mockProps.gotoPage.mockReset();
    });

    it('calls gotoPage', () => {
      shallow(
        <PageExplorerPanel
          {...mockProps}
          path={[1]}
          page={{ children: { items: [1] } }}
          nodes={{
            1: {
              id: 1,
              admin_display_title: 'Test',
              meta: { status: {}, type: 'test' },
            },
          }}
        />,
      )
        .find('PageExplorerItem')
        .prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).toHaveBeenCalled();
    });
  });

  describe('hooks', () => {
    it('componentWillReceiveProps push', () => {
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      expect(wrapper.setProps({ depth: 2 }).state('transition')).toBe('push');
    });

    it('componentWillReceiveProps pop', () => {
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      expect(wrapper.setProps({ depth: 0 }).state('transition')).toBe('pop');
    });
  });

  describe('clickOutsideDeactivates', () => {
    afterEach(() => {
      document.body.innerHTML = '';
    });

    const getClickOutsideDeactivates = (wrapper) =>
      wrapper.find('FocusTrap').prop('focusTrapOptions')
        .clickOutsideDeactivates;

    it('returns false (does not deactivate) when click target is the Pages menu button', () => {
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      const clickOutsideDeactivates = getClickOutsideDeactivates(wrapper);

      const button = document.createElement('button');
      const menuItem = document.createElement('div');
      menuItem.className = 'sidebar-page-explorer-item';
      menuItem.appendChild(button);
      document.body.appendChild(menuItem);

      expect(clickOutsideDeactivates({ target: button })).toBe(false);
    });

    it('returns true (deactivates) when click target is outside the Pages menu button', () => {
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      const clickOutsideDeactivates = getClickOutsideDeactivates(wrapper);

      const outsideEl = document.createElement('div');
      document.body.appendChild(outsideEl);

      expect(clickOutsideDeactivates({ target: outsideEl })).toBe(true);
    });
  });
});
