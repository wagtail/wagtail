const registry = {
  decorators: {},
  blocks: {},
  sources: {},
};

const registerDecorators = (decorators) => {
  Object.assign(registry.decorators, decorators);
};

const getDecorator = name => registry.decorators[name];

const registerBlocks = (blocks) => {
  Object.assign(registry.blocks, blocks);
};

const getBlock = name => registry.blocks[name];

const registerSources = (sources) => {
  Object.assign(registry.sources, sources);
};

const getSource = name => registry.sources[name];

export default {
  registerDecorators,
  getDecorator,
  registerBlocks,
  getBlock,
  registerSources,
  getSource,
};
