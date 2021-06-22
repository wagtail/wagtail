import React from 'react';
import { shallow } from 'enzyme';
import PageExplorerPanel from './PageExplorerPanel';

const mockProps = {
  page: {
    children: {
      items: [],
    },
    meta: {
      parent: null
    }
  },
  depth: 1,
  onClose: jest.fn(),
  gotoPage: jest.fn(),
  nodes: {},
};

describe('PageExplorerPanel', () => {
  describe('general rendering', () => {
    beforeEach(() => {
      document.body.innerHTML = '<div data-explorer-menu-item></div>';
    });

    it('exists', () => {
      expect(PageExplorerPanel).toBeDefined();
    });

    it('renders', () => {
      expect(shallow(<PageExplorerPanel {...mockProps} />)).toMatchSnapshot();
    });

    it('#isFetching', () => {
      expect(shallow((
        <PageExplorerPanel
          {...mockProps}
          page={Object.assign({ isFetching: true }, mockProps.page)}
        />
      ))).toMatchSnapshot();
    });

    it('#isError', () => {
      expect(shallow((
        <PageExplorerPanel
          {...mockProps}
          page={Object.assign({ isError: true }, mockProps.page)}
        />
      ))).toMatchSnapshot();
    });

    it('no children', () => {
      expect(shallow((
        <PageExplorerPanel
          {...mockProps}
          page={{ children: {} }}
        />
      ))).toMatchSnapshot();
    });

    it('#items', () => {
      expect(shallow((
        <PageExplorerPanel
          {...mockProps}
          page={{ children: { items: [1, 2] } }}
          nodes={{
            1: { id: 1, admin_display_title: 'Test', meta: { status: {}, type: 'test' } },
            2: { id: 2, admin_display_title: 'Foo', meta: { status: {}, type: 'foo' } },
          }}
        />
      ))).toMatchSnapshot();
    });
  });

  describe('onHeaderClick', () => {
    beforeEach(() => {
      mockProps.gotoPage.mockReset();
    });

    it('calls gotoPage', () => {
      shallow((
        <PageExplorerPanel {...mockProps} depth={2} page={{ children: { items: [] }, meta: { parent: { id: 1 } } }} />
      )).find('PageExplorerHeader').prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).toHaveBeenCalled();
    });

    it('does not call gotoPage for first page', () => {
      shallow((
        <PageExplorerPanel {...mockProps} depth={0} page={{ children: { items: [] }, meta: {  parent: { id: 1 } } }} />
      )).find('PageExplorerHeader').prop('onClick')({
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
      shallow((
        <PageExplorerPanel
          {...mockProps}
          path={[1]}
          page={{ children: { items: [1] } }}
          nodes={{ 1: { id: 1, admin_display_title: 'Test', meta: { status: {}, type: 'test' } } }}
        />
      )).find('PageExplorerItem').prop('onClick')({
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

  describe('clickOutside', () => {
    afterEach(() => {
      mockProps.onClose.mockReset();
    });

    it('triggers onClose when click is outside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu></div><div id="t"></div>';
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).toHaveBeenCalled();
    });

    it('does not trigger onClose when click is inside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu><div id="t"></div></div>';
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).not.toHaveBeenCalled();
    });

    it('pauses focus trap inside toggle', () => {
      document.body.innerHTML = '<div data-explorer-menu-item><div id="t"></div></div><div data-explorer-menu></div>';
      const wrapper = shallow(<PageExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(wrapper.state('paused')).toEqual(true);
    });
  });
});
