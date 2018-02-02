import registry from './registry';

describe('registry', () => {
  describe('sources', () => {
    it('works', () => {
      expect(registry.getSource('UndefinedSource')).not.toBeDefined();

      registry.registerSources({
        TestSource: null,
      });

      expect(registry.getSource('TestSource')).toBe(null);
    });
  });

  describe('decorators', () => {
    it('works', () => {
      expect(registry.getDecorator('UndefinedDecorator')).not.toBeDefined();

      registry.registerDecorators({
        TestDecorator: null,
      });

      expect(registry.getDecorator('TestDecorator')).toBe(null);
    });
  });

  describe('blocks', () => {
    it('works', () => {
      expect(registry.getBlock('UndefinedBlock')).not.toBeDefined();

      registry.registerBlocks({
        TestBlock: null,
      });

      expect(registry.getBlock('TestBlock')).toBe(null);
    });
  });
});
