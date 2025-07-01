import axe from 'axe-core';
import { Readability } from '@mozilla/readability';

/**
 * Raw options for Readability.js.
 */
type ReadabilityOptions<T = string> = ConstructorParameters<
  typeof Readability<T>
>[1];

/**
 * Options for extracting content with Readability.js.
 * See https://github.com/mozilla/readability#new-readabilitydocument-options
 * for more details. Note that only JSON-serializable options are supported,
 * as the options are passed to the iframe via `postMessage`. This means that
 * the `serializer` option is not supported.
 */
export type ExtractorOptions<T = string> = Omit<
  NonNullable<ReadabilityOptions<T>>,
  'serializer'
>;

/**
 * A Readability.js `Article` object.
 * See https://github.com/mozilla/readability#parse for more details.
 */
export type ExtractedContent = ReturnType<Readability['parse']>;

/**
 * Axe plugin instance for extracting content from the preview iframe
 * using Readability.js.
 * This plugin is registered in the `wagtailPreview` registry.
 */
export const contentExtractorPluginInstance = {
  id: 'extractor',
  extract(
    options: ExtractorOptions | undefined,
    callback: (content: ExtractedContent) => void,
  ) {
    const content = new Readability(
      document.cloneNode(true) as Document,
      options,
    ).parse();
    callback(content);
  },
};

/**
 * Calls the `extract` method in the `extractor` plugin instance of the `wagtailPreview` registry.
 * Wrapped in a promise so we can use async/await syntax instead of callbacks
 */
export const getExtractedContent = (
  options?: ExtractorOptions,
): Promise<ExtractedContent> =>
  new Promise((resolve) => {
    axe.plugins.wagtailPreview.run(
      'extractor',
      'extract',
      options,
      (content: ExtractedContent) => {
        resolve(content);
      },
    );
  });
