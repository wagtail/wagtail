import registry from './registry';

describe('registry', () => {
  it('works', () => {
    const plugin = {
      type: 'TEST',
      source: null,
      decorator: null,
    };

    expect(registry.getPlugin('TEST')).not.toBeDefined();
    registry.registerPlugin(plugin);
    expect(registry.getPlugin('TEST')).toBe(plugin);
  });
});
