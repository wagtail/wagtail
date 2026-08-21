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

    it('keeps the focus trap active when the page explorer button is clicked', () => {
      document.body.innerHTML = `
        <li class="sidebar-page-explorer-item"><button type="button"></button></li>
      `;
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      const clickOutsideDeactivates = wrapper
        .find('FocusTrap')
        .prop('focusTrapOptions').clickOutsideDeactivates;

      expect(
        clickOutsideDeactivates({ target: document.querySelector('button') }),
      ).toBe(false);
      expect(clickOutsideDeactivates({ target: document.body })).toBe(true);
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
});
