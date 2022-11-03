function initTagField(id, autocompleteUrl, options) {
  const finalOptions = {
    autocomplete: { source: autocompleteUrl },
    preprocessTag(val) {
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
}
