import { setAttrs } from './attrs';

describe('setAttrs', () => {
  let element;
  beforeEach(() => {
    document.body.innerHTML = /* html */ `
      <div id="one" data-existing-attribute="hello">
      </div>
    `;
    element = document.getElementById('one');
  });

  it('should not do anything with an empty object', () => {
    setAttrs(element, {});
    expect(element.getAttribute('data-existing-attribute')).toEqual('hello');
    expect(element.id).toEqual('one');
  });

  it('should set the values as string', () => {
    setAttrs(element, {
      'data-one': '1',
      'data-two': true,
      'data-three': false,
      'data-four': 2,
    });
    expect(element.getAttribute('data-one')).toEqual('1');
    expect(element.getAttribute('data-two')).toEqual('true');
    expect(element.getAttribute('data-three')).toEqual('false');
    expect(element.getAttribute('data-four')).toEqual('2');
    expect(element.getAttribute('data-existing-attribute')).toEqual('hello');
    expect(element.id).toEqual('one');
  });

  it('should overwrite existing attributes', () => {
    setAttrs(element, {
      'data-existing-attribute': 'world',
    });
    expect(element.getAttribute('data-existing-attribute')).toEqual('world');
    expect(element.id).toEqual('one');
  });
});
