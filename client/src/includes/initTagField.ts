import $ from 'jquery';

declare global {
  interface JQuery {
    tagit(...args): void;
  }
}

/**
 * Initialises the tag fields using the jQuery tagit widget
 *
 * @param id - element id to initialise against
 * @param source -  auto complete URL source
 * @param options - Other options passed to jQuery tagit
 */
const initTagField = (
  id: string,
  source: string,
  options: Record<string, any>,
): void => {
  const tagFieldElement = document.getElementById(id);

  if (!tagFieldElement) return;

  const finalOptions = {
    autocomplete: { source },
    preprocessTag(val: any) {
      // Double quote a tag if it contains a space
      // and if it isn't already quoted.
      if (val && val[0] !== '"' && val.indexOf(' ') > -1) {
        return '"' + val + '"';
      }

      return val;
    },
    ...options,
  };

  $('#' + id).tagit(finalOptions);
};

export { initTagField };
