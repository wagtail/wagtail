import { compareVersion } from './version';

it('returns something', () => {
  const result = compareVersion('1.12', '1.11');

  expect(result).toBe(1);
});
