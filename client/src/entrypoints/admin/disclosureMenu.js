// JavaScript source code
/*
*   This content is licensed according to the W3C Software License at
*   https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document
*
*   Supplemental JS for the disclosure menu keyboard behavior
*/

// const { current } = require("../../../../../node_modules/immer/dist/internal");


var DisclosureNav = function (domNode) {
  this.rootNode = domNode;
  this.triggerNodes = [];
  this.controlledNodes = [];
  this.openIndex = null;
  this.useArrowKeys = true;
};

DisclosureNav.prototype.init = function () {
  var buttons = this.rootNode.querySelectorAll('div[aria-expanded][aria-controls]');
  var button = null;
  var menu = null;

  for (let i = 0; i < buttons.length; i++) {
    button = buttons[i];
    menu = button.parentNode.querySelector('ul');
    if (menu) {
      // save ref to button and controlled menu
      this.triggerNodes.push(button);
      this.controlledNodes.push(menu);

      // collapse menus
      button.setAttribute('aria-expanded', 'false');
      this.toggleMenu(menu, false);

      // attach event listeners
      menu.addEventListener('keydown', this.handleMenuKeyDown.bind(this));
      button.addEventListener('click', this.handleButtonClick.bind(this));
      button.addEventListener('keydown', this.handleButtonKeyDown.bind(this));
    }
  }
  this.rootNode.addEventListener('focusout', this.handleBlur.bind(this));
};

DisclosureNav.prototype.toggleMenu = function (domNode, show) {
  var button = domNode;
  if (domNode) {
    button.style.display = show ? 'block' : 'none';
  }
};

DisclosureNav.prototype.toggleExpand = function (index, expanded) {
  var btindex = 0;
  // handle menu at called index
  if (this.triggerNodes[btindex]) {
    this.openIndex = expanded ? btindex : null;
    for (let i = 0; i < this.triggerNodes.length; i++) {
      this.triggerNodes[i].setAttribute('aria-expanded', expanded);
    }
    this.toggleMenu(this.controlledNodes[btindex], expanded);
  }
};

DisclosureNav.prototype.controlFocusByKey = function (keyboardEvent, nodeList, currentIndex) {
  var prevIndex = null;
  var nextIndex = null;
  switch (keyboardEvent.key) {
  case 'ArrowUp':
  case 'ArrowLeft':
    keyboardEvent.preventDefault();
    if (currentIndex > -1) {
      prevIndex = Math.max(0, currentIndex - 1);
      nodeList[prevIndex].focus();
    }
    break;
  case 'ArrowDown':
  case 'ArrowRight':
    keyboardEvent.preventDefault();
    if (currentIndex > -1) {
      nextIndex = Math.min(nodeList.length - 1, currentIndex + 1);
      nodeList[nextIndex].focus();
    }
    break;
  case 'Home':
    keyboardEvent.preventDefault();
    nodeList[0].focus();
    break;
  case 'End':
    keyboardEvent.preventDefault();
    nodeList[nodeList.length - 1].focus();
    break;
  default:
  }
};

/* Event Handlers */
DisclosureNav.prototype.handleBlur = function (event) {
  var menuContainsFocus = this.rootNode.contains(event.relatedTarget);
  if (!menuContainsFocus && this.openIndex !== null) {
    this.toggleExpand(this.openIndex, false);
  }
};

DisclosureNav.prototype.handleButtonKeyDown = function (event) {
  var targetButtonIndex = this.triggerNodes.indexOf(document.activeElement);

  if (event.key === 'Escape') {
    this.toggleExpand(this.openIndex, false);
    this.triggerNodes[targetButtonIndex].parentNode.setAttribute('class',
      'dropdown dropup dropdown-button match-width');
  } else if (event.key === 'Enter') {
    this.toggleExpand(this.openIndex, true);
    this.triggerNodes[targetButtonIndex].parentNode.setAttribute('class',
      'dropdown dropup dropdown-button match-width open');
  } else if (this.useArrowKeys && this.openIndex === targetButtonIndex && event.key === 'ArrowDown') {
    event.preventDefault();
    this.controlledNodes[this.openIndex].querySelector('a, button').focus();
  } else if (this.useArrowKeys) { // handle arrow key navigation between top-level buttons, if set
    this.controlFocusByKey(event, this.triggerNodes, targetButtonIndex);
  }
};

DisclosureNav.prototype.handleButtonClick = function (event) {
  var buttonIndex = 0;
  var buttonExpanded = this.triggerNodes[buttonIndex].getAttribute('aria-expanded') === 'true';
  this.toggleExpand(buttonIndex, !buttonExpanded);
};

DisclosureNav.prototype.handleMenuKeyDown = function (event) {
  var menuLinks = Array.prototype.slice.call(
    this.controlledNodes[this.openIndex].querySelectorAll('a, button'));
  var currentIndex = menuLinks.indexOf(document.activeElement);
  var button = this.triggerNodes[this.openIndex].parentNode;
  if (this.openIndex === null) {
    return;
  }

  // close on escape
  if (event.key === 'Escape') {
    this.triggerNodes[this.openIndex].focus();
    this.toggleExpand(this.openIndex, false);
    button.setAttribute('class', 'dropdown dropup dropdown-button match-width');
  } else if (this.useArrowKeys) { // handle arrow key navigation within menu links, if set
    this.controlFocusByKey(event, menuLinks, currentIndex);
  }
};

// switch on/off arrow key navigation
DisclosureNav.prototype.updateKeyControls = function (useArrowKeys) {
  this.useArrowKeys = useArrowKeys;
};

/* Initialize Disclosure Menus */
window.addEventListener('load', (event) => {
  var menus = document.querySelectorAll('.disclosure-nav');
  var disclosureMenus = [];
  var checked = true;

  for (let i = 0; i < menus.length; i++) {
    disclosureMenus[i] = new DisclosureNav(menus[i]);
    disclosureMenus[i].init();
  }

  for (let j = 0; j < disclosureMenus.length; j++) {
    disclosureMenus[j].updateKeyControls(checked);
  }
}, false);
