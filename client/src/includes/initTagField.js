import $ from 'jquery';
import { escapeHtml } from '../../utils/text';

/* generic function for adding a message to message area through JS alone */
function addMessage(status, text) {
  $('.messages')
    .addClass('new')
    .empty()
    .append('<ul><li class="' + status + '">' + text + '</li></ul>');
  const addMsgTimeout = setTimeout(() => {
    $('.messages').addClass('appear');
    clearTimeout(addMsgTimeout);
  }, 100);
}

window.addMessage = addMessage;

window.escapeHtml = escapeHtml;

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

window.initTagField = initTagField;
/* generic function for adding a message to message area through JS alone end */