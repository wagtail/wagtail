import React from 'react';
import { shallow } from 'enzyme';

import EditorFallback from './EditorFallback';

describe('EditorFallback', () => {
  it('works', () => {
    expect(
      shallow(
        <EditorFallback field={document.createElement('input')}>
          test
        </EditorFallback>,
      ),
    ).toMatchSnapshot();
  });

  it('#componentDidCatch', () => {
    const field = document.createElement('input');
    field.value = 'test value';

    const wrapper = shallow(
      <EditorFallback field={field}>test</EditorFallback>,
    );

    field.value = 'new test value';

    const error = new Error('test');
    const info = { componentStack: 'test' };

    wrapper.instance().componentDidCatch(error, info);

    expect(wrapper.state('error')).toBe(error);
    expect(wrapper.state('info')).toBe(info);
    expect(field.value).toBe('test value');
  });

  describe('#error', () => {
    it('works', () => {
      const wrapper = shallow(
        <EditorFallback field={document.createElement('input')}>
          test
        </EditorFallback>,
      );

      wrapper.setState({
        error: new Error('test'),
      });

      expect(wrapper).toMatchSnapshot();
    });

    it('reload', () => {
      const wrapper = shallow(
        <EditorFallback field={document.createElement('input')}>
          test
        </EditorFallback>,
      );

      wrapper
        .setState({
          error: new Error('test'),
        })
        .find('button')
        .last()
        .simulate('click');

      expect(wrapper).toMatchSnapshot();
    });

    it('reload page', () => {
      delete window.location;
      window.location = { reload: jest.fn() };

      const wrapper = shallow(
        <EditorFallback field={document.createElement('input')}>
          test
        </EditorFallback>,
      );

      wrapper
        .setState({
          error: new Error('test'),
          reloads: 3,
        })
        .find('button')
        .last()
        .simulate('click');

      expect(global.location.reload).toHaveBeenCalled();
    });

    it('#showError', () => {
      const wrapper = shallow(
        <EditorFallback field={document.createElement('input')}>
          test
        </EditorFallback>,
      );

      const error = new Error('test');

      error.stack = 'test stack';

      wrapper
        .setState({
          error: error,
          info: { componentStack: 'test' },
        })
        .find('button')
        .first()
        .simulate('click');

      expect(wrapper).toMatchSnapshot();
    });

    it('#showContent', () => {
      const field = document.createElement('input');
      field.rawContentState = {
        entityMap: {},
        blocks: [
          {
            key: 'a',
            text: 'test',
          },
        ],
      };

      const wrapper = shallow(
        <EditorFallback field={field}>test</EditorFallback>,
      );

      const error = new Error('test');
      error.stack = 'test stack';

      wrapper
        .setState({
          error: error,
          info: { componentStack: 'test' },
        })
        .find('button')
        .first()
        .simulate('click');

      expect(wrapper).toMatchSnapshot();
    });
  });
});
