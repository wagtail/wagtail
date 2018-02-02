const registry = {
  decorators: {},
  blocks: {},
  sources: {},
};

const registerDecorators = (decorators) => Object.assign(registry.decorators, decorators);
const registerBlocks = (blocks) => Object.assign(registry.blocks, blocks);
const registerSources = (sources) => Object.assign(registry.sources, sources);

const getDecorator = name => registry.decorators[name];
const getBlock = name => registry.blocks[name];
const getSource = name => registry.sources[name];

export default {
  registerDecorators,
  registerBlocks,
  registerSources,
  getDecorator,
  getBlock,
  getSource,
};
