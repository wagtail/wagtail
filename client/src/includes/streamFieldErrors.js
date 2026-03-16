import { escapeHtml as h } from '../utils/text';

const removeErrorMessages = (container) => {
  container
    .querySelectorAll(':scope > .help-block.help-critical')
    .forEach((element) => element.remove());
};

const addErrorMessages = (container, messages) => {
  messages.forEach((message) => {
    const errorElement = document.createElement('p');
    errorElement.classList.add('help-block');
    errorElement.classList.add('help-critical');
    errorElement.innerHTML = h(message);
    container.insertBefore(errorElement, container.childNodes[0]);
  });
};

const removeWarningMessages = (container) => {
  container
    .querySelectorAll(':scope > .help-block.help-warning')
    .forEach((element) => element.remove());
};

const addWarningMessages = (container, messages) => {
  messages.forEach((message) => {
    const warningElement = document.createElement('p');
    warningElement.classList.add('help-block');
    warningElement.classList.add('help-warning');
    warningElement.innerHTML = h(message);
    container.insertBefore(warningElement, container.childNodes[0]);
  });
};

export {
  addErrorMessages,
  removeErrorMessages,
  addWarningMessages,
  removeWarningMessages,
};
