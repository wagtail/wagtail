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
  isVisible: true,
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

  describe('FocusTrap pausing behaviour', () => {
    // Regression tests for: page explorer re-opens after being closed.
    // Root cause: FocusTrap fired onDeactivate during the slide-out animation
    // because it was still active while isVisible=false.
    // Fix: pause the trap whenever isVisible is false.

    it('pauses FocusTrap when isVisible is false (panel closing / slide-out animation)', () => {
      const wrapper = shallow(
        <PageExplorerPanel {...mockProps} isVisible={false} />,
      );
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(true);
    });

    it('does not pause FocusTrap when isVisible is true and page is ready', () => {
      const wrapper = shallow(
        <PageExplorerPanel {...mockProps} isVisible={true} />,
      );
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(false);
    });

    it('pauses FocusTrap when isFetchingChildren is true even if isVisible is true', () => {
      const wrapper = shallow(
        <PageExplorerPanel
          {...mockProps}
          isVisible={true}
          page={{ ...mockProps.page, isFetchingChildren: true }}
        />,
      );
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(true);
    });

    it('pauses FocusTrap when isFetchingTranslations is true even if isVisible is true', () => {
      const wrapper = shallow(
        <PageExplorerPanel
          {...mockProps}
          isVisible={true}
          page={{ ...mockProps.page, isFetchingTranslations: true }}
        />,
      );
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(true);
    });

    it('transitions FocusTrap from active to paused when isVisible changes to false', () => {
      const wrapper = shallow(
        <PageExplorerPanel {...mockProps} isVisible={true} />,
      );
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(false);

      wrapper.setProps({ isVisible: false });
      expect(wrapper.find('FocusTrap').prop('paused')).toBe(true);
    });
  });
});
