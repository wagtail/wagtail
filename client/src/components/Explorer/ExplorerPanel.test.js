import React from 'react';
import { shallow } from 'enzyme';
import ExplorerPanel from './ExplorerPanel';

const mockProps = {
  page: {
    children: {
      items: [],
    },
  },
  onClose: jest.fn(),
  path: [],
  popPage: jest.fn(),
  pushPage: jest.fn(),
  nodes: {},
};

describe('ExplorerPanel', () => {
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

  describe('onHeaderClick', () => {
    beforeEach(() => {
      mockProps.popPage.mockReset();
    });

    it('calls popPage', () => {
      shallow((
        <ExplorerPanel {...mockProps} path={[1, 2, 3]} />
      )).find('ExplorerHeader').prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.popPage).toHaveBeenCalled();
    });

    it('does not call popPage for first page', () => {
      shallow((
        <ExplorerPanel {...mockProps} path={[1]} />
      )).find('ExplorerHeader').prop('onClick')({
        preventDefault() {},
        stopPropagation() {},
      });

      expect(mockProps.popPage).not.toHaveBeenCalled();
    });
  });

  describe('onItemClick', () => {
    beforeEach(() => {
      mockProps.pushPage.mockReset();
    });

    it('calls pushPage', () => {
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

      expect(mockProps.pushPage).toHaveBeenCalled();
    });
  });

  describe('hooks', () => {
    let wrapper;

    beforeEach(() => {
      wrapper = shallow(<ExplorerPanel {...mockProps} />);
    });

    it('componentWillReceiveProps push', () => {
      expect(wrapper.setProps({ path: [1] }).state('transition')).toBe('push');
    });

    it('componentWillReceiveProps pop', () => {
      expect(wrapper.setProps({ path: [] }).state('transition')).toBe('pop');
    });

    it('componentDidMount', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div>';
      wrapper.instance().componentDidMount();
      expect(document.querySelector('[data-explorer-menu-item]').classList.contains('submenu-active')).toBe(true);
      expect(document.body.classList.contains('explorer-open')).toBe(true);
    });

    it('componentWillUnmount', () => {
      document.body.innerHTML = '<div class="submenu-active" data-explorer-menu-item></div>';
      wrapper.instance().componentWillUnmount();
      expect(document.querySelector('[data-explorer-menu-item]').classList.contains('submenu-active')).toBe(false);
      expect(document.body.classList.contains('explorer-open')).toBe(false);
    });
  });

  describe('clickOutside', () => {
    let wrapper;

    beforeEach(() => {
      wrapper = shallow(<ExplorerPanel {...mockProps} />);
    });

    afterEach(() => {
      mockProps.onClose.mockReset();
    });

    it('triggers onClose when click is outside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu></div><div id="t"></div>';
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).toHaveBeenCalled();
    });

    it('does not trigger onClose when click is inside', () => {
      document.body.innerHTML = '<div data-explorer-menu-item></div><div data-explorer-menu><div id="t"></div></div>';
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(mockProps.onClose).not.toHaveBeenCalled();
    });

    it('pauses focus trap inside toggle', () => {
      document.body.innerHTML = '<div data-explorer-menu-item><div id="t"></div></div><div data-explorer-menu></div>';
      wrapper.instance().clickOutside({
        target: document.querySelector('#t'),
      });
      expect(wrapper.state('paused')).toEqual(true);
    });
  });
});
