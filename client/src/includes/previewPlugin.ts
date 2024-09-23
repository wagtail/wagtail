import axe, { AxePlugin } from 'axe-core';

/**
 * Axe plugin registry for interaction between the page editor and the live preview.
 * Compared to other aspects of Axe and other plugins,
 * - The parent frame only triggers execution of the plugin’s logic in the one frame.
 * - The preview frame only executes the plugin’s logic, it doesn’t go through its own frames.
 * See https://github.com/dequelabs/axe-core/blob/master/doc/plugins.md.
 */
export const wagtailPreviewPlugin: AxePlugin = {
  id: 'wagtailPreview',
  run(id, action, options, callback) {
    // Outside the preview frame, we need to send the command to the preview iframe.
    const preview = document.getElementById(
      'w-preview-iframe',
    ) as HTMLIFrameElement;

    if (preview) {
      // @ts-expect-error Not declared in the official Axe Utils API.
      axe.utils.sendCommandToFrame(
        preview,
        {
          command: 'run-wagtailPreview',
          parameter: id,
          action: action,
          options: options,
        },
        (results) => {
          // Pass the results from the preview iframe to the callback.
          callback(results);
        },
      );
    } else {
      // Inside the preview frame, only call the expected plugin instance method.
      // eslint-disable-next-line no-underscore-dangle
      const pluginInstance = this._registry[id];
      pluginInstance?.[action].call(pluginInstance, options, callback);
    }
  },
  commands: [
    {
      id: 'run-wagtailPreview',
      callback(data, callback) {
        return axe.plugins.wagtailPreview.run(
          data.parameter,
          data.action,
          data.options,
          callback,
        );
      },
    },
  ],
};
