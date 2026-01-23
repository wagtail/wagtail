import { identity } from './identity';

describe('identity', () => {
  it('should return undefined if not called with anything', () => {
    expect(identity()).toEqual(undefined);
  });

  it('should return the first value from multiple args supplied', () => {
    expect(identity('wagtail', 'bird', 'sans')).toEqual('wagtail');
  });
});
