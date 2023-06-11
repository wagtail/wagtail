import { isDateEqual } from './date';

describe('isDateEqual', () => {
  it('should return undefined if given invalid values', () => {
    expect(isDateEqual()).toEqual(undefined);
  });

  it('should return true if the dates are equal (ignoring time)', () => {
    expect(isDateEqual(new Date(), new Date())).toBe(true);
    expect(isDateEqual(new Date('2024-04-05'), new Date('2024-04-05'))).toBe(
      true,
    );
    expect(
      isDateEqual(new Date('2024-04-05T10:00'), new Date('2024-04-05T11:00')),
    ).toBe(true);
  });

  it('should return false if the dates are not equal', () => {
    expect(isDateEqual(new Date(), new Date('2024-04-05'))).toBe(false);
    expect(isDateEqual(new Date('2024-04-06'), new Date('2024-04-05'))).toBe(
      false,
    );
  });
});
