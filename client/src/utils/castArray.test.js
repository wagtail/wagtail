import { castArray } from './castArray';

describe('castArray', () => {
  it('should return an empty array by default', () => {
    expect(castArray()).toEqual([]);
  });

  it('should the provided argument wrapped as an array if it is not one', () => {
    expect(castArray(null)).toEqual([null]);
    expect(castArray(undefined)).toEqual([undefined]);
    expect(castArray(3)).toEqual([3]);
  });

  it('should return the provided argument as an array if it is one', () => {
    expect(castArray([])).toEqual([]);
    expect(castArray([1, 2, 3])).toEqual([1, 2, 3]);
    expect(castArray([1, 2, ['nested', 'true']])).toEqual([
      1,
      2,
      ['nested', 'true'],
    ]);
  });

  it('should return a set of arguments as an array', () => {
    expect(castArray(1, 2, 3)).toEqual([1, 2, 3]);
    expect(castArray(null, undefined)).toEqual([null, undefined]);
  });
});
