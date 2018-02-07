const plugins = {};

const registerPlugin = (plugin) => {
  plugins[plugin.type] = plugin;

  return plugins;
};

const getPlugin = (type) => plugins[type];

export default {
  registerPlugin,
  getPlugin,
};
