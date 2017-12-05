const registry = {
  decorators: {},
  sources: {},
  strategies: {},
};

const registerDecorators = (decorators) => {
  Object.assign(registry.decorators, decorators);
};

const getDecorator = name => registry.decorators[name];

const registerSources = (sources) => {
  Object.assign(registry.sources, sources);
};

const getSource = name => registry.sources[name];

const registerStrategies = (strategies) => {
  Object.assign(registry.strategies, strategies);
};

const getStrategy = name => registry.strategies[name];

export default {
  registerDecorators,
  getDecorator,
  registerSources,
  getSource,
  registerStrategies,
  getStrategy,
};
