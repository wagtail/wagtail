import React from 'react';
import { shallow } from 'enzyme';
import ExplorerPanel from './ExplorerPanel';

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

describe('ExplorerPanel', () => {
  describe('general rendering', () => {
    beforeEach(() => {
      document.body.innerHTML = '<div data-explorer-menu-item></div>';
    });

    it('exists', () => {
      expect(ExplorerPanel).toBeDefined();
    });

    it('renders', () => {
      expect(shallow(<ExplorerPanel {...mockProps} />)).toMatchSnapshot();
    });

    it('#isFetching', () => {
      expect(shallow((
        <ExplorerPanel
          {...mockProps}
          page={Object.assign({ isFetching: true }, mockProps.page)}
        />
      ))).toMatchSnapshot();
    });

    it('#isError', () => {
      expect(shallow((
        <ExplorerPanel
          {...mockProps}
          page={Object.assign({ isError: true }, mockProps.page)}
        />
      ))).toMatchSnapshot();
    });

    it('no children', () => {
      expect(shallow((
        <ExplorerPanel
          {...mockProps}
          page={{ children: {} }}
        />
      ))).toMatchSnapshot();
    });

    it('#items', () => {
      expect(shallow((
        <ExplorerPanel
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
        <ExplorerPanel {...mockProps} depth={2} page={{ children: { items: [] }, meta: { parent: { id: 1 } } }} />
      )).find('ExplorerHeader').prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).toHaveBeenCalled();
    });

    it('does not call gotoPage for first page', () => {
      shallow((
        <ExplorerPanel {...mockProps} depth={0} page={{ children: { items: [] }, meta: {  parent: { id: 1 } } }} />
      )).find('ExplorerHeader').prop('onClick')({
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
        <ExplorerPanel
          {...mockProps}
          path={[1]}
          page={{ children: { items: [1] } }}
          nodes={{ 1: { id: 1, admin_display_title: 'Test', meta: { status: {}, type: 'test' } } }}
        />
      )).find('ExplorerItem').prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.gotoPage).toHaveBeenCalled();
    });
  });

  describe('hooks', () => {
    it('componentWillReceiveProps push', () => {
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      expect(wrapper.setProps({ depth: 2 }).state('transition')).toBe('push');
    });

    it('componentWillReceiveProps pop', () => {
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      expect(wrapper.setProps({ depth: 0 }).state('transition')).toBe('pop');
    });

    it('componentDidMount', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div>';
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      wrapper.instance().componentDidMount();
      expect(document.querySelector('[data-explorer-menu-item]').classList.contains('submenu-active')).toBe(true);
      expect(document.body.classList.contains('explorer-open')).toBe(true);
    });

    it('componentWillUnmount', () => {
      document.body.innerHTML = '<div class="submenu-active" data-explorer-menu-item></div>';
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      wrapper.instance().componentWillUnmount();
      expect(document.querySelector('[data-explorer-menu-item]').classList.contains('submenu-active')).toBe(false);
      expect(document.body.classList.contains('explorer-open')).toBe(false);
    });
  });

  describe('clickOutside', () => {
    afterEach(() => {
      mockProps.onClose.mockReset();
    });

    it('triggers onClose when click is outside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu></div><div id="t"></div>';
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).toHaveBeenCalled();
    });

    it('does not trigger onClose when click is inside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu><div id="t"></div></div>';
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).not.toHaveBeenCalled();
    });

    it('pauses focus trap inside toggle', () => {
      document.body.innerHTML = '<div data-explorer-menu-item><div id="t"></div></div><div data-explorer-menu></div>';
      const wrapper = shallow(<ExplorerPanel {...mockProps} />);
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(wrapper.state('paused')).toEqual(true);
    });
  });
});
