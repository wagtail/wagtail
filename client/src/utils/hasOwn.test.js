import { hasOwn } from './hasOwn';

describe('hasOwn', () => {
  it('should return false when not provided an object', () => {
    expect(hasOwn()).toEqual(false);
    expect(hasOwn(null)).toEqual(false);
    expect(hasOwn([])).toEqual(false);
    expect(hasOwn(undefined)).toEqual(false);
  });

  it('should return false if the object does not have the key', () => {
    expect(hasOwn({}, 'a')).toEqual(false);
    expect(hasOwn({ bb: true }, 'a')).toEqual(false);
    expect(hasOwn({ AA: 'something' }, 'aa')).toEqual(false);
  });

  it('should return true if the object does  have the key', () => {
    expect(hasOwn({ bb: true }, 'bb')).toEqual(true);
    expect(hasOwn({ AA: 'something' }, 'AA')).toEqual(true);
  });
});
