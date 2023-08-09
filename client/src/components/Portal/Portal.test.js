import React from 'react';
import { shallow, mount } from 'enzyme';
import Portal from './Portal';

const func = expect.any(Function);

describe('Portal', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  it('empty', () => {
    expect(mount(<Portal onClose={() => {}} />)).toMatchSnapshot();
  });

  it('#children', () => {
    expect(mount(<Portal onClose={() => {}}>Test!</Portal>)).toMatchSnapshot();
  });

  it('component lifecycle', () => {
    document.removeEventListener = jest.fn();
    window.removeEventListener = jest.fn();

    const wrapper = mount(<Portal onClose={() => {}}>Test!</Portal>);

    expect(document.body.innerHTML).toMatchSnapshot();

    wrapper.instance().componentWillUnmount();

    expect(document.body.innerHTML).toBe('');

    expect(document.removeEventListener).toHaveBeenCalledWith('mouseup', func);
    expect(document.removeEventListener).toHaveBeenCalledWith('keyup', func);
    expect(window.removeEventListener).toHaveBeenCalledWith('resize', func);

    document.removeEventListener.mockRestore();
    window.removeEventListener.mockRestore();
  });

  describe('#onClose', () => {
    beforeEach(() => {
      jest.spyOn(document, 'addEventListener');
      jest.spyOn(window, 'addEventListener');
    });

    afterEach(() => {
      document.removeEventListener.mockRestore();
      window.removeEventListener.mockRestore();
    });

    it('#closeOnClick', () => {
      const onClose = jest.fn();
      shallow(
        <Portal onClose={onClose} closeOnClick>
          Test!
        </Portal>,
      );
      expect(document.addEventListener).toHaveBeenCalledWith('mouseup', func);
    });

    it('#closeOnType', () => {
      const onClose = jest.fn();
      shallow(
        <Portal onClose={onClose} closeOnType>
          Test!
        </Portal>,
      );
      expect(document.addEventListener).toHaveBeenCalledWith('keyup', func);
    });

    it('#closeOnResize', () => {
      const onClose = jest.fn();
      shallow(
        <Portal onClose={onClose} closeOnResize>
          Test!
        </Portal>,
      );
      expect(window.addEventListener).toHaveBeenCalledWith('resize', func);
    });
  });

  describe('onCloseEvent', () => {
    it('should close', () => {
      const onClose = jest.fn();
      const wrapper = mount(<Portal onClose={onClose}>Test!</Portal>);
      const target = document.createElement('div');

      wrapper.instance().onCloseEvent({ target });

      expect(onClose).toHaveBeenCalled();
    });

    it('not should close', () => {
      const onClose = jest.fn();
      const wrapper = mount(
        <Portal onClose={onClose}>
          <div id="test">Test</div>
        </Portal>,
      );
      const target = document.querySelector('#test');

      wrapper.instance().onCloseEvent({ target });

      expect(onClose).not.toHaveBeenCalled();
    });
  });
});
