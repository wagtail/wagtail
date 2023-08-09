import { range } from './range';

describe('range', () => {
  it('should return an empty array if no data provided', () => {
    expect(range()).toEqual([]);
  });

  it('should return an array of numbers from start to, but not including, end', () => {
    expect(range(0, 1)).toEqual([0]);
    expect(range(2, 7)).toEqual([2, 3, 4, 5, 6]);
    expect(range(0, 3)).toEqual([0, 1, 2]);
    expect(range(1, 3)).toEqual([1, 2]);
  });
});
