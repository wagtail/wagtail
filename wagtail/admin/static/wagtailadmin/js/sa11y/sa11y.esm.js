var top = 'top';
var bottom = 'bottom';
var right = 'right';
var left = 'left';
var auto = 'auto';
var basePlacements = [top, bottom, right, left];
var start = 'start';
var end = 'end';
var clippingParents = 'clippingParents';
var viewport = 'viewport';
var popper = 'popper';
var reference = 'reference';
var variationPlacements = /*#__PURE__*/basePlacements.reduce(function (acc, placement) {
  return acc.concat([placement + "-" + start, placement + "-" + end]);
}, []);
var placements = /*#__PURE__*/[].concat(basePlacements, [auto]).reduce(function (acc, placement) {
  return acc.concat([placement, placement + "-" + start, placement + "-" + end]);
}, []); // modifiers that need to read the DOM

var beforeRead = 'beforeRead';
var read = 'read';
var afterRead = 'afterRead'; // pure-logic modifiers

var beforeMain = 'beforeMain';
var main = 'main';
var afterMain = 'afterMain'; // modifier with the purpose to write to the DOM (or write into a framework state)

var beforeWrite = 'beforeWrite';
var write = 'write';
var afterWrite = 'afterWrite';
var modifierPhases = [beforeRead, read, afterRead, beforeMain, main, afterMain, beforeWrite, write, afterWrite];

function getNodeName(element) {
  return element ? (element.nodeName || '').toLowerCase() : null;
}

function getWindow(node) {
  if (node == null) {
    return window;
  }

  if (node.toString() !== '[object Window]') {
    var ownerDocument = node.ownerDocument;
    return ownerDocument ? ownerDocument.defaultView || window : window;
  }

  return node;
}

function isElement$1(node) {
  var OwnElement = getWindow(node).Element;
  return node instanceof OwnElement || node instanceof Element;
}

function isHTMLElement(node) {
  var OwnElement = getWindow(node).HTMLElement;
  return node instanceof OwnElement || node instanceof HTMLElement;
}

function isShadowRoot(node) {
  // IE 11 has no ShadowRoot
  if (typeof ShadowRoot === 'undefined') {
    return false;
  }

  var OwnElement = getWindow(node).ShadowRoot;
  return node instanceof OwnElement || node instanceof ShadowRoot;
}

// and applies them to the HTMLElements such as popper and arrow

function applyStyles(_ref) {
  var state = _ref.state;
  Object.keys(state.elements).forEach(function (name) {
    var style = state.styles[name] || {};
    var attributes = state.attributes[name] || {};
    var element = state.elements[name]; // arrow is optional + virtual elements

    if (!isHTMLElement(element) || !getNodeName(element)) {
      return;
    } // Flow doesn't support to extend this property, but it's the most
    // effective way to apply styles to an HTMLElement
    // $FlowFixMe[cannot-write]


    Object.assign(element.style, style);
    Object.keys(attributes).forEach(function (name) {
      var value = attributes[name];

      if (value === false) {
        element.removeAttribute(name);
      } else {
        element.setAttribute(name, value === true ? '' : value);
      }
    });
  });
}

function effect$2(_ref2) {
  var state = _ref2.state;
  var initialStyles = {
    popper: {
      position: state.options.strategy,
      left: '0',
      top: '0',
      margin: '0'
    },
    arrow: {
      position: 'absolute'
    },
    reference: {}
  };
  Object.assign(state.elements.popper.style, initialStyles.popper);
  state.styles = initialStyles;

  if (state.elements.arrow) {
    Object.assign(state.elements.arrow.style, initialStyles.arrow);
  }

  return function () {
    Object.keys(state.elements).forEach(function (name) {
      var element = state.elements[name];
      var attributes = state.attributes[name] || {};
      var styleProperties = Object.keys(state.styles.hasOwnProperty(name) ? state.styles[name] : initialStyles[name]); // Set all values to an empty string to unset them

      var style = styleProperties.reduce(function (style, property) {
        style[property] = '';
        return style;
      }, {}); // arrow is optional + virtual elements

      if (!isHTMLElement(element) || !getNodeName(element)) {
        return;
      }

      Object.assign(element.style, style);
      Object.keys(attributes).forEach(function (attribute) {
        element.removeAttribute(attribute);
      });
    });
  };
} // eslint-disable-next-line import/no-unused-modules


var applyStyles$1 = {
  name: 'applyStyles',
  enabled: true,
  phase: 'write',
  fn: applyStyles,
  effect: effect$2,
  requires: ['computeStyles']
};

function getBasePlacement$1(placement) {
  return placement.split('-')[0];
}

var max = Math.max;
var min = Math.min;
var round = Math.round;

function getUAString() {
  var uaData = navigator.userAgentData;

  if (uaData != null && uaData.brands) {
    return uaData.brands.map(function (item) {
      return item.brand + "/" + item.version;
    }).join(' ');
  }

  return navigator.userAgent;
}

function isLayoutViewport() {
  return !/^((?!chrome|android).)*safari/i.test(getUAString());
}

function getBoundingClientRect(element, includeScale, isFixedStrategy) {
  if (includeScale === void 0) {
    includeScale = false;
  }

  if (isFixedStrategy === void 0) {
    isFixedStrategy = false;
  }

  var clientRect = element.getBoundingClientRect();
  var scaleX = 1;
  var scaleY = 1;

  if (includeScale && isHTMLElement(element)) {
    scaleX = element.offsetWidth > 0 ? round(clientRect.width) / element.offsetWidth || 1 : 1;
    scaleY = element.offsetHeight > 0 ? round(clientRect.height) / element.offsetHeight || 1 : 1;
  }

  var _ref = isElement$1(element) ? getWindow(element) : window,
      visualViewport = _ref.visualViewport;

  var addVisualOffsets = !isLayoutViewport() && isFixedStrategy;
  var x = (clientRect.left + (addVisualOffsets && visualViewport ? visualViewport.offsetLeft : 0)) / scaleX;
  var y = (clientRect.top + (addVisualOffsets && visualViewport ? visualViewport.offsetTop : 0)) / scaleY;
  var width = clientRect.width / scaleX;
  var height = clientRect.height / scaleY;
  return {
    width: width,
    height: height,
    top: y,
    right: x + width,
    bottom: y + height,
    left: x,
    x: x,
    y: y
  };
}

// means it doesn't take into account transforms.

function getLayoutRect(element) {
  var clientRect = getBoundingClientRect(element); // Use the clientRect sizes if it's not been transformed.
  // Fixes https://github.com/popperjs/popper-core/issues/1223

  var width = element.offsetWidth;
  var height = element.offsetHeight;

  if (Math.abs(clientRect.width - width) <= 1) {
    width = clientRect.width;
  }

  if (Math.abs(clientRect.height - height) <= 1) {
    height = clientRect.height;
  }

  return {
    x: element.offsetLeft,
    y: element.offsetTop,
    width: width,
    height: height
  };
}

function contains(parent, child) {
  var rootNode = child.getRootNode && child.getRootNode(); // First, attempt with faster native method

  if (parent.contains(child)) {
    return true;
  } // then fallback to custom implementation with Shadow DOM support
  else if (rootNode && isShadowRoot(rootNode)) {
      var next = child;

      do {
        if (next && parent.isSameNode(next)) {
          return true;
        } // $FlowFixMe[prop-missing]: need a better way to handle this...


        next = next.parentNode || next.host;
      } while (next);
    } // Give up, the result is false


  return false;
}

function getComputedStyle$1(element) {
  return getWindow(element).getComputedStyle(element);
}

function isTableElement(element) {
  return ['table', 'td', 'th'].indexOf(getNodeName(element)) >= 0;
}

function getDocumentElement(element) {
  // $FlowFixMe[incompatible-return]: assume body is always available
  return ((isElement$1(element) ? element.ownerDocument : // $FlowFixMe[prop-missing]
  element.document) || window.document).documentElement;
}

function getParentNode(element) {
  if (getNodeName(element) === 'html') {
    return element;
  }

  return (// this is a quicker (but less type safe) way to save quite some bytes from the bundle
    // $FlowFixMe[incompatible-return]
    // $FlowFixMe[prop-missing]
    element.assignedSlot || // step into the shadow DOM of the parent of a slotted node
    element.parentNode || ( // DOM Element detected
    isShadowRoot(element) ? element.host : null) || // ShadowRoot detected
    // $FlowFixMe[incompatible-call]: HTMLElement is a Node
    getDocumentElement(element) // fallback

  );
}

function getTrueOffsetParent(element) {
  if (!isHTMLElement(element) || // https://github.com/popperjs/popper-core/issues/837
  getComputedStyle$1(element).position === 'fixed') {
    return null;
  }

  return element.offsetParent;
} // `.offsetParent` reports `null` for fixed elements, while absolute elements
// return the containing block


function getContainingBlock(element) {
  var isFirefox = /firefox/i.test(getUAString());
  var isIE = /Trident/i.test(getUAString());

  if (isIE && isHTMLElement(element)) {
    // In IE 9, 10 and 11 fixed elements containing block is always established by the viewport
    var elementCss = getComputedStyle$1(element);

    if (elementCss.position === 'fixed') {
      return null;
    }
  }

  var currentNode = getParentNode(element);

  if (isShadowRoot(currentNode)) {
    currentNode = currentNode.host;
  }

  while (isHTMLElement(currentNode) && ['html', 'body'].indexOf(getNodeName(currentNode)) < 0) {
    var css = getComputedStyle$1(currentNode); // This is non-exhaustive but covers the most common CSS properties that
    // create a containing block.
    // https://developer.mozilla.org/en-US/docs/Web/CSS/Containing_block#identifying_the_containing_block

    if (css.transform !== 'none' || css.perspective !== 'none' || css.contain === 'paint' || ['transform', 'perspective'].indexOf(css.willChange) !== -1 || isFirefox && css.willChange === 'filter' || isFirefox && css.filter && css.filter !== 'none') {
      return currentNode;
    } else {
      currentNode = currentNode.parentNode;
    }
  }

  return null;
} // Gets the closest ancestor positioned element. Handles some edge cases,
// such as table ancestors and cross browser bugs.


function getOffsetParent(element) {
  var window = getWindow(element);
  var offsetParent = getTrueOffsetParent(element);

  while (offsetParent && isTableElement(offsetParent) && getComputedStyle$1(offsetParent).position === 'static') {
    offsetParent = getTrueOffsetParent(offsetParent);
  }

  if (offsetParent && (getNodeName(offsetParent) === 'html' || getNodeName(offsetParent) === 'body' && getComputedStyle$1(offsetParent).position === 'static')) {
    return window;
  }

  return offsetParent || getContainingBlock(element) || window;
}

function getMainAxisFromPlacement(placement) {
  return ['top', 'bottom'].indexOf(placement) >= 0 ? 'x' : 'y';
}

function within(min$1, value, max$1) {
  return max(min$1, min(value, max$1));
}
function withinMaxClamp(min, value, max) {
  var v = within(min, value, max);
  return v > max ? max : v;
}

function getFreshSideObject() {
  return {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0
  };
}

function mergePaddingObject(paddingObject) {
  return Object.assign({}, getFreshSideObject(), paddingObject);
}

function expandToHashMap(value, keys) {
  return keys.reduce(function (hashMap, key) {
    hashMap[key] = value;
    return hashMap;
  }, {});
}

var toPaddingObject = function toPaddingObject(padding, state) {
  padding = typeof padding === 'function' ? padding(Object.assign({}, state.rects, {
    placement: state.placement
  })) : padding;
  return mergePaddingObject(typeof padding !== 'number' ? padding : expandToHashMap(padding, basePlacements));
};

function arrow(_ref) {
  var _state$modifiersData$;

  var state = _ref.state,
      name = _ref.name,
      options = _ref.options;
  var arrowElement = state.elements.arrow;
  var popperOffsets = state.modifiersData.popperOffsets;
  var basePlacement = getBasePlacement$1(state.placement);
  var axis = getMainAxisFromPlacement(basePlacement);
  var isVertical = [left, right].indexOf(basePlacement) >= 0;
  var len = isVertical ? 'height' : 'width';

  if (!arrowElement || !popperOffsets) {
    return;
  }

  var paddingObject = toPaddingObject(options.padding, state);
  var arrowRect = getLayoutRect(arrowElement);
  var minProp = axis === 'y' ? top : left;
  var maxProp = axis === 'y' ? bottom : right;
  var endDiff = state.rects.reference[len] + state.rects.reference[axis] - popperOffsets[axis] - state.rects.popper[len];
  var startDiff = popperOffsets[axis] - state.rects.reference[axis];
  var arrowOffsetParent = getOffsetParent(arrowElement);
  var clientSize = arrowOffsetParent ? axis === 'y' ? arrowOffsetParent.clientHeight || 0 : arrowOffsetParent.clientWidth || 0 : 0;
  var centerToReference = endDiff / 2 - startDiff / 2; // Make sure the arrow doesn't overflow the popper if the center point is
  // outside of the popper bounds

  var min = paddingObject[minProp];
  var max = clientSize - arrowRect[len] - paddingObject[maxProp];
  var center = clientSize / 2 - arrowRect[len] / 2 + centerToReference;
  var offset = within(min, center, max); // Prevents breaking syntax highlighting...

  var axisProp = axis;
  state.modifiersData[name] = (_state$modifiersData$ = {}, _state$modifiersData$[axisProp] = offset, _state$modifiersData$.centerOffset = offset - center, _state$modifiersData$);
}

function effect$1(_ref2) {
  var state = _ref2.state,
      options = _ref2.options;
  var _options$element = options.element,
      arrowElement = _options$element === void 0 ? '[data-popper-arrow]' : _options$element;

  if (arrowElement == null) {
    return;
  } // CSS selector


  if (typeof arrowElement === 'string') {
    arrowElement = state.elements.popper.querySelector(arrowElement);

    if (!arrowElement) {
      return;
    }
  }

  if (!contains(state.elements.popper, arrowElement)) {

    return;
  }

  state.elements.arrow = arrowElement;
} // eslint-disable-next-line import/no-unused-modules


var arrow$1 = {
  name: 'arrow',
  enabled: true,
  phase: 'main',
  fn: arrow,
  effect: effect$1,
  requires: ['popperOffsets'],
  requiresIfExists: ['preventOverflow']
};

function getVariation(placement) {
  return placement.split('-')[1];
}

var unsetSides = {
  top: 'auto',
  right: 'auto',
  bottom: 'auto',
  left: 'auto'
}; // Round the offsets to the nearest suitable subpixel based on the DPR.
// Zooming can change the DPR, but it seems to report a value that will
// cleanly divide the values into the appropriate subpixels.

function roundOffsetsByDPR(_ref) {
  var x = _ref.x,
      y = _ref.y;
  var win = window;
  var dpr = win.devicePixelRatio || 1;
  return {
    x: round(x * dpr) / dpr || 0,
    y: round(y * dpr) / dpr || 0
  };
}

function mapToStyles(_ref2) {
  var _Object$assign2;

  var popper = _ref2.popper,
      popperRect = _ref2.popperRect,
      placement = _ref2.placement,
      variation = _ref2.variation,
      offsets = _ref2.offsets,
      position = _ref2.position,
      gpuAcceleration = _ref2.gpuAcceleration,
      adaptive = _ref2.adaptive,
      roundOffsets = _ref2.roundOffsets,
      isFixed = _ref2.isFixed;
  var _offsets$x = offsets.x,
      x = _offsets$x === void 0 ? 0 : _offsets$x,
      _offsets$y = offsets.y,
      y = _offsets$y === void 0 ? 0 : _offsets$y;

  var _ref3 = typeof roundOffsets === 'function' ? roundOffsets({
    x: x,
    y: y
  }) : {
    x: x,
    y: y
  };

  x = _ref3.x;
  y = _ref3.y;
  var hasX = offsets.hasOwnProperty('x');
  var hasY = offsets.hasOwnProperty('y');
  var sideX = left;
  var sideY = top;
  var win = window;

  if (adaptive) {
    var offsetParent = getOffsetParent(popper);
    var heightProp = 'clientHeight';
    var widthProp = 'clientWidth';

    if (offsetParent === getWindow(popper)) {
      offsetParent = getDocumentElement(popper);

      if (getComputedStyle$1(offsetParent).position !== 'static' && position === 'absolute') {
        heightProp = 'scrollHeight';
        widthProp = 'scrollWidth';
      }
    } // $FlowFixMe[incompatible-cast]: force type refinement, we compare offsetParent with window above, but Flow doesn't detect it


    offsetParent = offsetParent;

    if (placement === top || (placement === left || placement === right) && variation === end) {
      sideY = bottom;
      var offsetY = isFixed && offsetParent === win && win.visualViewport ? win.visualViewport.height : // $FlowFixMe[prop-missing]
      offsetParent[heightProp];
      y -= offsetY - popperRect.height;
      y *= gpuAcceleration ? 1 : -1;
    }

    if (placement === left || (placement === top || placement === bottom) && variation === end) {
      sideX = right;
      var offsetX = isFixed && offsetParent === win && win.visualViewport ? win.visualViewport.width : // $FlowFixMe[prop-missing]
      offsetParent[widthProp];
      x -= offsetX - popperRect.width;
      x *= gpuAcceleration ? 1 : -1;
    }
  }

  var commonStyles = Object.assign({
    position: position
  }, adaptive && unsetSides);

  var _ref4 = roundOffsets === true ? roundOffsetsByDPR({
    x: x,
    y: y
  }) : {
    x: x,
    y: y
  };

  x = _ref4.x;
  y = _ref4.y;

  if (gpuAcceleration) {
    var _Object$assign;

    return Object.assign({}, commonStyles, (_Object$assign = {}, _Object$assign[sideY] = hasY ? '0' : '', _Object$assign[sideX] = hasX ? '0' : '', _Object$assign.transform = (win.devicePixelRatio || 1) <= 1 ? "translate(" + x + "px, " + y + "px)" : "translate3d(" + x + "px, " + y + "px, 0)", _Object$assign));
  }

  return Object.assign({}, commonStyles, (_Object$assign2 = {}, _Object$assign2[sideY] = hasY ? y + "px" : '', _Object$assign2[sideX] = hasX ? x + "px" : '', _Object$assign2.transform = '', _Object$assign2));
}

function computeStyles(_ref5) {
  var state = _ref5.state,
      options = _ref5.options;
  var _options$gpuAccelerat = options.gpuAcceleration,
      gpuAcceleration = _options$gpuAccelerat === void 0 ? true : _options$gpuAccelerat,
      _options$adaptive = options.adaptive,
      adaptive = _options$adaptive === void 0 ? true : _options$adaptive,
      _options$roundOffsets = options.roundOffsets,
      roundOffsets = _options$roundOffsets === void 0 ? true : _options$roundOffsets;

  var commonStyles = {
    placement: getBasePlacement$1(state.placement),
    variation: getVariation(state.placement),
    popper: state.elements.popper,
    popperRect: state.rects.popper,
    gpuAcceleration: gpuAcceleration,
    isFixed: state.options.strategy === 'fixed'
  };

  if (state.modifiersData.popperOffsets != null) {
    state.styles.popper = Object.assign({}, state.styles.popper, mapToStyles(Object.assign({}, commonStyles, {
      offsets: state.modifiersData.popperOffsets,
      position: state.options.strategy,
      adaptive: adaptive,
      roundOffsets: roundOffsets
    })));
  }

  if (state.modifiersData.arrow != null) {
    state.styles.arrow = Object.assign({}, state.styles.arrow, mapToStyles(Object.assign({}, commonStyles, {
      offsets: state.modifiersData.arrow,
      position: 'absolute',
      adaptive: false,
      roundOffsets: roundOffsets
    })));
  }

  state.attributes.popper = Object.assign({}, state.attributes.popper, {
    'data-popper-placement': state.placement
  });
} // eslint-disable-next-line import/no-unused-modules


var computeStyles$1 = {
  name: 'computeStyles',
  enabled: true,
  phase: 'beforeWrite',
  fn: computeStyles,
  data: {}
};

var passive = {
  passive: true
};

function effect(_ref) {
  var state = _ref.state,
      instance = _ref.instance,
      options = _ref.options;
  var _options$scroll = options.scroll,
      scroll = _options$scroll === void 0 ? true : _options$scroll,
      _options$resize = options.resize,
      resize = _options$resize === void 0 ? true : _options$resize;
  var window = getWindow(state.elements.popper);
  var scrollParents = [].concat(state.scrollParents.reference, state.scrollParents.popper);

  if (scroll) {
    scrollParents.forEach(function (scrollParent) {
      scrollParent.addEventListener('scroll', instance.update, passive);
    });
  }

  if (resize) {
    window.addEventListener('resize', instance.update, passive);
  }

  return function () {
    if (scroll) {
      scrollParents.forEach(function (scrollParent) {
        scrollParent.removeEventListener('scroll', instance.update, passive);
      });
    }

    if (resize) {
      window.removeEventListener('resize', instance.update, passive);
    }
  };
} // eslint-disable-next-line import/no-unused-modules


var eventListeners = {
  name: 'eventListeners',
  enabled: true,
  phase: 'write',
  fn: function fn() {},
  effect: effect,
  data: {}
};

var hash$1 = {
  left: 'right',
  right: 'left',
  bottom: 'top',
  top: 'bottom'
};
function getOppositePlacement(placement) {
  return placement.replace(/left|right|bottom|top/g, function (matched) {
    return hash$1[matched];
  });
}

var hash = {
  start: 'end',
  end: 'start'
};
function getOppositeVariationPlacement(placement) {
  return placement.replace(/start|end/g, function (matched) {
    return hash[matched];
  });
}

function getWindowScroll(node) {
  var win = getWindow(node);
  var scrollLeft = win.pageXOffset;
  var scrollTop = win.pageYOffset;
  return {
    scrollLeft: scrollLeft,
    scrollTop: scrollTop
  };
}

function getWindowScrollBarX(element) {
  // If <html> has a CSS width greater than the viewport, then this will be
  // incorrect for RTL.
  // Popper 1 is broken in this case and never had a bug report so let's assume
  // it's not an issue. I don't think anyone ever specifies width on <html>
  // anyway.
  // Browsers where the left scrollbar doesn't cause an issue report `0` for
  // this (e.g. Edge 2019, IE11, Safari)
  return getBoundingClientRect(getDocumentElement(element)).left + getWindowScroll(element).scrollLeft;
}

function getViewportRect(element, strategy) {
  var win = getWindow(element);
  var html = getDocumentElement(element);
  var visualViewport = win.visualViewport;
  var width = html.clientWidth;
  var height = html.clientHeight;
  var x = 0;
  var y = 0;

  if (visualViewport) {
    width = visualViewport.width;
    height = visualViewport.height;
    var layoutViewport = isLayoutViewport();

    if (layoutViewport || !layoutViewport && strategy === 'fixed') {
      x = visualViewport.offsetLeft;
      y = visualViewport.offsetTop;
    }
  }

  return {
    width: width,
    height: height,
    x: x + getWindowScrollBarX(element),
    y: y
  };
}

// of the `<html>` and `<body>` rect bounds if horizontally scrollable

function getDocumentRect(element) {
  var _element$ownerDocumen;

  var html = getDocumentElement(element);
  var winScroll = getWindowScroll(element);
  var body = (_element$ownerDocumen = element.ownerDocument) == null ? void 0 : _element$ownerDocumen.body;
  var width = max(html.scrollWidth, html.clientWidth, body ? body.scrollWidth : 0, body ? body.clientWidth : 0);
  var height = max(html.scrollHeight, html.clientHeight, body ? body.scrollHeight : 0, body ? body.clientHeight : 0);
  var x = -winScroll.scrollLeft + getWindowScrollBarX(element);
  var y = -winScroll.scrollTop;

  if (getComputedStyle$1(body || html).direction === 'rtl') {
    x += max(html.clientWidth, body ? body.clientWidth : 0) - width;
  }

  return {
    width: width,
    height: height,
    x: x,
    y: y
  };
}

function isScrollParent(element) {
  // Firefox wants us to check `-x` and `-y` variations as well
  var _getComputedStyle = getComputedStyle$1(element),
      overflow = _getComputedStyle.overflow,
      overflowX = _getComputedStyle.overflowX,
      overflowY = _getComputedStyle.overflowY;

  return /auto|scroll|overlay|hidden/.test(overflow + overflowY + overflowX);
}

function getScrollParent(node) {
  if (['html', 'body', '#document'].indexOf(getNodeName(node)) >= 0) {
    // $FlowFixMe[incompatible-return]: assume body is always available
    return node.ownerDocument.body;
  }

  if (isHTMLElement(node) && isScrollParent(node)) {
    return node;
  }

  return getScrollParent(getParentNode(node));
}

/*
given a DOM element, return the list of all scroll parents, up the list of ancesors
until we get to the top window object. This list is what we attach scroll listeners
to, because if any of these parent elements scroll, we'll need to re-calculate the
reference element's position.
*/

function listScrollParents(element, list) {
  var _element$ownerDocumen;

  if (list === void 0) {
    list = [];
  }

  var scrollParent = getScrollParent(element);
  var isBody = scrollParent === ((_element$ownerDocumen = element.ownerDocument) == null ? void 0 : _element$ownerDocumen.body);
  var win = getWindow(scrollParent);
  var target = isBody ? [win].concat(win.visualViewport || [], isScrollParent(scrollParent) ? scrollParent : []) : scrollParent;
  var updatedList = list.concat(target);
  return isBody ? updatedList : // $FlowFixMe[incompatible-call]: isBody tells us target will be an HTMLElement here
  updatedList.concat(listScrollParents(getParentNode(target)));
}

function rectToClientRect(rect) {
  return Object.assign({}, rect, {
    left: rect.x,
    top: rect.y,
    right: rect.x + rect.width,
    bottom: rect.y + rect.height
  });
}

function getInnerBoundingClientRect(element, strategy) {
  var rect = getBoundingClientRect(element, false, strategy === 'fixed');
  rect.top = rect.top + element.clientTop;
  rect.left = rect.left + element.clientLeft;
  rect.bottom = rect.top + element.clientHeight;
  rect.right = rect.left + element.clientWidth;
  rect.width = element.clientWidth;
  rect.height = element.clientHeight;
  rect.x = rect.left;
  rect.y = rect.top;
  return rect;
}

function getClientRectFromMixedType(element, clippingParent, strategy) {
  return clippingParent === viewport ? rectToClientRect(getViewportRect(element, strategy)) : isElement$1(clippingParent) ? getInnerBoundingClientRect(clippingParent, strategy) : rectToClientRect(getDocumentRect(getDocumentElement(element)));
} // A "clipping parent" is an overflowable container with the characteristic of
// clipping (or hiding) overflowing elements with a position different from
// `initial`


function getClippingParents(element) {
  var clippingParents = listScrollParents(getParentNode(element));
  var canEscapeClipping = ['absolute', 'fixed'].indexOf(getComputedStyle$1(element).position) >= 0;
  var clipperElement = canEscapeClipping && isHTMLElement(element) ? getOffsetParent(element) : element;

  if (!isElement$1(clipperElement)) {
    return [];
  } // $FlowFixMe[incompatible-return]: https://github.com/facebook/flow/issues/1414


  return clippingParents.filter(function (clippingParent) {
    return isElement$1(clippingParent) && contains(clippingParent, clipperElement) && getNodeName(clippingParent) !== 'body';
  });
} // Gets the maximum area that the element is visible in due to any number of
// clipping parents


function getClippingRect(element, boundary, rootBoundary, strategy) {
  var mainClippingParents = boundary === 'clippingParents' ? getClippingParents(element) : [].concat(boundary);
  var clippingParents = [].concat(mainClippingParents, [rootBoundary]);
  var firstClippingParent = clippingParents[0];
  var clippingRect = clippingParents.reduce(function (accRect, clippingParent) {
    var rect = getClientRectFromMixedType(element, clippingParent, strategy);
    accRect.top = max(rect.top, accRect.top);
    accRect.right = min(rect.right, accRect.right);
    accRect.bottom = min(rect.bottom, accRect.bottom);
    accRect.left = max(rect.left, accRect.left);
    return accRect;
  }, getClientRectFromMixedType(element, firstClippingParent, strategy));
  clippingRect.width = clippingRect.right - clippingRect.left;
  clippingRect.height = clippingRect.bottom - clippingRect.top;
  clippingRect.x = clippingRect.left;
  clippingRect.y = clippingRect.top;
  return clippingRect;
}

function computeOffsets(_ref) {
  var reference = _ref.reference,
      element = _ref.element,
      placement = _ref.placement;
  var basePlacement = placement ? getBasePlacement$1(placement) : null;
  var variation = placement ? getVariation(placement) : null;
  var commonX = reference.x + reference.width / 2 - element.width / 2;
  var commonY = reference.y + reference.height / 2 - element.height / 2;
  var offsets;

  switch (basePlacement) {
    case top:
      offsets = {
        x: commonX,
        y: reference.y - element.height
      };
      break;

    case bottom:
      offsets = {
        x: commonX,
        y: reference.y + reference.height
      };
      break;

    case right:
      offsets = {
        x: reference.x + reference.width,
        y: commonY
      };
      break;

    case left:
      offsets = {
        x: reference.x - element.width,
        y: commonY
      };
      break;

    default:
      offsets = {
        x: reference.x,
        y: reference.y
      };
  }

  var mainAxis = basePlacement ? getMainAxisFromPlacement(basePlacement) : null;

  if (mainAxis != null) {
    var len = mainAxis === 'y' ? 'height' : 'width';

    switch (variation) {
      case start:
        offsets[mainAxis] = offsets[mainAxis] - (reference[len] / 2 - element[len] / 2);
        break;

      case end:
        offsets[mainAxis] = offsets[mainAxis] + (reference[len] / 2 - element[len] / 2);
        break;
    }
  }

  return offsets;
}

function detectOverflow(state, options) {
  if (options === void 0) {
    options = {};
  }

  var _options = options,
      _options$placement = _options.placement,
      placement = _options$placement === void 0 ? state.placement : _options$placement,
      _options$strategy = _options.strategy,
      strategy = _options$strategy === void 0 ? state.strategy : _options$strategy,
      _options$boundary = _options.boundary,
      boundary = _options$boundary === void 0 ? clippingParents : _options$boundary,
      _options$rootBoundary = _options.rootBoundary,
      rootBoundary = _options$rootBoundary === void 0 ? viewport : _options$rootBoundary,
      _options$elementConte = _options.elementContext,
      elementContext = _options$elementConte === void 0 ? popper : _options$elementConte,
      _options$altBoundary = _options.altBoundary,
      altBoundary = _options$altBoundary === void 0 ? false : _options$altBoundary,
      _options$padding = _options.padding,
      padding = _options$padding === void 0 ? 0 : _options$padding;
  var paddingObject = mergePaddingObject(typeof padding !== 'number' ? padding : expandToHashMap(padding, basePlacements));
  var altContext = elementContext === popper ? reference : popper;
  var popperRect = state.rects.popper;
  var element = state.elements[altBoundary ? altContext : elementContext];
  var clippingClientRect = getClippingRect(isElement$1(element) ? element : element.contextElement || getDocumentElement(state.elements.popper), boundary, rootBoundary, strategy);
  var referenceClientRect = getBoundingClientRect(state.elements.reference);
  var popperOffsets = computeOffsets({
    reference: referenceClientRect,
    element: popperRect,
    strategy: 'absolute',
    placement: placement
  });
  var popperClientRect = rectToClientRect(Object.assign({}, popperRect, popperOffsets));
  var elementClientRect = elementContext === popper ? popperClientRect : referenceClientRect; // positive = overflowing the clipping rect
  // 0 or negative = within the clipping rect

  var overflowOffsets = {
    top: clippingClientRect.top - elementClientRect.top + paddingObject.top,
    bottom: elementClientRect.bottom - clippingClientRect.bottom + paddingObject.bottom,
    left: clippingClientRect.left - elementClientRect.left + paddingObject.left,
    right: elementClientRect.right - clippingClientRect.right + paddingObject.right
  };
  var offsetData = state.modifiersData.offset; // Offsets can be applied only to the popper element

  if (elementContext === popper && offsetData) {
    var offset = offsetData[placement];
    Object.keys(overflowOffsets).forEach(function (key) {
      var multiply = [right, bottom].indexOf(key) >= 0 ? 1 : -1;
      var axis = [top, bottom].indexOf(key) >= 0 ? 'y' : 'x';
      overflowOffsets[key] += offset[axis] * multiply;
    });
  }

  return overflowOffsets;
}

function computeAutoPlacement(state, options) {
  if (options === void 0) {
    options = {};
  }

  var _options = options,
      placement = _options.placement,
      boundary = _options.boundary,
      rootBoundary = _options.rootBoundary,
      padding = _options.padding,
      flipVariations = _options.flipVariations,
      _options$allowedAutoP = _options.allowedAutoPlacements,
      allowedAutoPlacements = _options$allowedAutoP === void 0 ? placements : _options$allowedAutoP;
  var variation = getVariation(placement);
  var placements$1 = variation ? flipVariations ? variationPlacements : variationPlacements.filter(function (placement) {
    return getVariation(placement) === variation;
  }) : basePlacements;
  var allowedPlacements = placements$1.filter(function (placement) {
    return allowedAutoPlacements.indexOf(placement) >= 0;
  });

  if (allowedPlacements.length === 0) {
    allowedPlacements = placements$1;
  } // $FlowFixMe[incompatible-type]: Flow seems to have problems with two array unions...


  var overflows = allowedPlacements.reduce(function (acc, placement) {
    acc[placement] = detectOverflow(state, {
      placement: placement,
      boundary: boundary,
      rootBoundary: rootBoundary,
      padding: padding
    })[getBasePlacement$1(placement)];
    return acc;
  }, {});
  return Object.keys(overflows).sort(function (a, b) {
    return overflows[a] - overflows[b];
  });
}

function getExpandedFallbackPlacements(placement) {
  if (getBasePlacement$1(placement) === auto) {
    return [];
  }

  var oppositePlacement = getOppositePlacement(placement);
  return [getOppositeVariationPlacement(placement), oppositePlacement, getOppositeVariationPlacement(oppositePlacement)];
}

function flip(_ref) {
  var state = _ref.state,
      options = _ref.options,
      name = _ref.name;

  if (state.modifiersData[name]._skip) {
    return;
  }

  var _options$mainAxis = options.mainAxis,
      checkMainAxis = _options$mainAxis === void 0 ? true : _options$mainAxis,
      _options$altAxis = options.altAxis,
      checkAltAxis = _options$altAxis === void 0 ? true : _options$altAxis,
      specifiedFallbackPlacements = options.fallbackPlacements,
      padding = options.padding,
      boundary = options.boundary,
      rootBoundary = options.rootBoundary,
      altBoundary = options.altBoundary,
      _options$flipVariatio = options.flipVariations,
      flipVariations = _options$flipVariatio === void 0 ? true : _options$flipVariatio,
      allowedAutoPlacements = options.allowedAutoPlacements;
  var preferredPlacement = state.options.placement;
  var basePlacement = getBasePlacement$1(preferredPlacement);
  var isBasePlacement = basePlacement === preferredPlacement;
  var fallbackPlacements = specifiedFallbackPlacements || (isBasePlacement || !flipVariations ? [getOppositePlacement(preferredPlacement)] : getExpandedFallbackPlacements(preferredPlacement));
  var placements = [preferredPlacement].concat(fallbackPlacements).reduce(function (acc, placement) {
    return acc.concat(getBasePlacement$1(placement) === auto ? computeAutoPlacement(state, {
      placement: placement,
      boundary: boundary,
      rootBoundary: rootBoundary,
      padding: padding,
      flipVariations: flipVariations,
      allowedAutoPlacements: allowedAutoPlacements
    }) : placement);
  }, []);
  var referenceRect = state.rects.reference;
  var popperRect = state.rects.popper;
  var checksMap = new Map();
  var makeFallbackChecks = true;
  var firstFittingPlacement = placements[0];

  for (var i = 0; i < placements.length; i++) {
    var placement = placements[i];

    var _basePlacement = getBasePlacement$1(placement);

    var isStartVariation = getVariation(placement) === start;
    var isVertical = [top, bottom].indexOf(_basePlacement) >= 0;
    var len = isVertical ? 'width' : 'height';
    var overflow = detectOverflow(state, {
      placement: placement,
      boundary: boundary,
      rootBoundary: rootBoundary,
      altBoundary: altBoundary,
      padding: padding
    });
    var mainVariationSide = isVertical ? isStartVariation ? right : left : isStartVariation ? bottom : top;

    if (referenceRect[len] > popperRect[len]) {
      mainVariationSide = getOppositePlacement(mainVariationSide);
    }

    var altVariationSide = getOppositePlacement(mainVariationSide);
    var checks = [];

    if (checkMainAxis) {
      checks.push(overflow[_basePlacement] <= 0);
    }

    if (checkAltAxis) {
      checks.push(overflow[mainVariationSide] <= 0, overflow[altVariationSide] <= 0);
    }

    if (checks.every(function (check) {
      return check;
    })) {
      firstFittingPlacement = placement;
      makeFallbackChecks = false;
      break;
    }

    checksMap.set(placement, checks);
  }

  if (makeFallbackChecks) {
    // `2` may be desired in some cases – research later
    var numberOfChecks = flipVariations ? 3 : 1;

    var _loop = function _loop(_i) {
      var fittingPlacement = placements.find(function (placement) {
        var checks = checksMap.get(placement);

        if (checks) {
          return checks.slice(0, _i).every(function (check) {
            return check;
          });
        }
      });

      if (fittingPlacement) {
        firstFittingPlacement = fittingPlacement;
        return "break";
      }
    };

    for (var _i = numberOfChecks; _i > 0; _i--) {
      var _ret = _loop(_i);

      if (_ret === "break") break;
    }
  }

  if (state.placement !== firstFittingPlacement) {
    state.modifiersData[name]._skip = true;
    state.placement = firstFittingPlacement;
    state.reset = true;
  }
} // eslint-disable-next-line import/no-unused-modules


var flip$1 = {
  name: 'flip',
  enabled: true,
  phase: 'main',
  fn: flip,
  requiresIfExists: ['offset'],
  data: {
    _skip: false
  }
};

function getSideOffsets(overflow, rect, preventedOffsets) {
  if (preventedOffsets === void 0) {
    preventedOffsets = {
      x: 0,
      y: 0
    };
  }

  return {
    top: overflow.top - rect.height - preventedOffsets.y,
    right: overflow.right - rect.width + preventedOffsets.x,
    bottom: overflow.bottom - rect.height + preventedOffsets.y,
    left: overflow.left - rect.width - preventedOffsets.x
  };
}

function isAnySideFullyClipped(overflow) {
  return [top, right, bottom, left].some(function (side) {
    return overflow[side] >= 0;
  });
}

function hide(_ref) {
  var state = _ref.state,
      name = _ref.name;
  var referenceRect = state.rects.reference;
  var popperRect = state.rects.popper;
  var preventedOffsets = state.modifiersData.preventOverflow;
  var referenceOverflow = detectOverflow(state, {
    elementContext: 'reference'
  });
  var popperAltOverflow = detectOverflow(state, {
    altBoundary: true
  });
  var referenceClippingOffsets = getSideOffsets(referenceOverflow, referenceRect);
  var popperEscapeOffsets = getSideOffsets(popperAltOverflow, popperRect, preventedOffsets);
  var isReferenceHidden = isAnySideFullyClipped(referenceClippingOffsets);
  var hasPopperEscaped = isAnySideFullyClipped(popperEscapeOffsets);
  state.modifiersData[name] = {
    referenceClippingOffsets: referenceClippingOffsets,
    popperEscapeOffsets: popperEscapeOffsets,
    isReferenceHidden: isReferenceHidden,
    hasPopperEscaped: hasPopperEscaped
  };
  state.attributes.popper = Object.assign({}, state.attributes.popper, {
    'data-popper-reference-hidden': isReferenceHidden,
    'data-popper-escaped': hasPopperEscaped
  });
} // eslint-disable-next-line import/no-unused-modules


var hide$1 = {
  name: 'hide',
  enabled: true,
  phase: 'main',
  requiresIfExists: ['preventOverflow'],
  fn: hide
};

function distanceAndSkiddingToXY(placement, rects, offset) {
  var basePlacement = getBasePlacement$1(placement);
  var invertDistance = [left, top].indexOf(basePlacement) >= 0 ? -1 : 1;

  var _ref = typeof offset === 'function' ? offset(Object.assign({}, rects, {
    placement: placement
  })) : offset,
      skidding = _ref[0],
      distance = _ref[1];

  skidding = skidding || 0;
  distance = (distance || 0) * invertDistance;
  return [left, right].indexOf(basePlacement) >= 0 ? {
    x: distance,
    y: skidding
  } : {
    x: skidding,
    y: distance
  };
}

function offset(_ref2) {
  var state = _ref2.state,
      options = _ref2.options,
      name = _ref2.name;
  var _options$offset = options.offset,
      offset = _options$offset === void 0 ? [0, 0] : _options$offset;
  var data = placements.reduce(function (acc, placement) {
    acc[placement] = distanceAndSkiddingToXY(placement, state.rects, offset);
    return acc;
  }, {});
  var _data$state$placement = data[state.placement],
      x = _data$state$placement.x,
      y = _data$state$placement.y;

  if (state.modifiersData.popperOffsets != null) {
    state.modifiersData.popperOffsets.x += x;
    state.modifiersData.popperOffsets.y += y;
  }

  state.modifiersData[name] = data;
} // eslint-disable-next-line import/no-unused-modules


var offset$1 = {
  name: 'offset',
  enabled: true,
  phase: 'main',
  requires: ['popperOffsets'],
  fn: offset
};

function popperOffsets(_ref) {
  var state = _ref.state,
      name = _ref.name;
  // Offsets are the actual position the popper needs to have to be
  // properly positioned near its reference element
  // This is the most basic placement, and will be adjusted by
  // the modifiers in the next step
  state.modifiersData[name] = computeOffsets({
    reference: state.rects.reference,
    element: state.rects.popper,
    strategy: 'absolute',
    placement: state.placement
  });
} // eslint-disable-next-line import/no-unused-modules


var popperOffsets$1 = {
  name: 'popperOffsets',
  enabled: true,
  phase: 'read',
  fn: popperOffsets,
  data: {}
};

function getAltAxis(axis) {
  return axis === 'x' ? 'y' : 'x';
}

function preventOverflow(_ref) {
  var state = _ref.state,
      options = _ref.options,
      name = _ref.name;
  var _options$mainAxis = options.mainAxis,
      checkMainAxis = _options$mainAxis === void 0 ? true : _options$mainAxis,
      _options$altAxis = options.altAxis,
      checkAltAxis = _options$altAxis === void 0 ? false : _options$altAxis,
      boundary = options.boundary,
      rootBoundary = options.rootBoundary,
      altBoundary = options.altBoundary,
      padding = options.padding,
      _options$tether = options.tether,
      tether = _options$tether === void 0 ? true : _options$tether,
      _options$tetherOffset = options.tetherOffset,
      tetherOffset = _options$tetherOffset === void 0 ? 0 : _options$tetherOffset;
  var overflow = detectOverflow(state, {
    boundary: boundary,
    rootBoundary: rootBoundary,
    padding: padding,
    altBoundary: altBoundary
  });
  var basePlacement = getBasePlacement$1(state.placement);
  var variation = getVariation(state.placement);
  var isBasePlacement = !variation;
  var mainAxis = getMainAxisFromPlacement(basePlacement);
  var altAxis = getAltAxis(mainAxis);
  var popperOffsets = state.modifiersData.popperOffsets;
  var referenceRect = state.rects.reference;
  var popperRect = state.rects.popper;
  var tetherOffsetValue = typeof tetherOffset === 'function' ? tetherOffset(Object.assign({}, state.rects, {
    placement: state.placement
  })) : tetherOffset;
  var normalizedTetherOffsetValue = typeof tetherOffsetValue === 'number' ? {
    mainAxis: tetherOffsetValue,
    altAxis: tetherOffsetValue
  } : Object.assign({
    mainAxis: 0,
    altAxis: 0
  }, tetherOffsetValue);
  var offsetModifierState = state.modifiersData.offset ? state.modifiersData.offset[state.placement] : null;
  var data = {
    x: 0,
    y: 0
  };

  if (!popperOffsets) {
    return;
  }

  if (checkMainAxis) {
    var _offsetModifierState$;

    var mainSide = mainAxis === 'y' ? top : left;
    var altSide = mainAxis === 'y' ? bottom : right;
    var len = mainAxis === 'y' ? 'height' : 'width';
    var offset = popperOffsets[mainAxis];
    var min$1 = offset + overflow[mainSide];
    var max$1 = offset - overflow[altSide];
    var additive = tether ? -popperRect[len] / 2 : 0;
    var minLen = variation === start ? referenceRect[len] : popperRect[len];
    var maxLen = variation === start ? -popperRect[len] : -referenceRect[len]; // We need to include the arrow in the calculation so the arrow doesn't go
    // outside the reference bounds

    var arrowElement = state.elements.arrow;
    var arrowRect = tether && arrowElement ? getLayoutRect(arrowElement) : {
      width: 0,
      height: 0
    };
    var arrowPaddingObject = state.modifiersData['arrow#persistent'] ? state.modifiersData['arrow#persistent'].padding : getFreshSideObject();
    var arrowPaddingMin = arrowPaddingObject[mainSide];
    var arrowPaddingMax = arrowPaddingObject[altSide]; // If the reference length is smaller than the arrow length, we don't want
    // to include its full size in the calculation. If the reference is small
    // and near the edge of a boundary, the popper can overflow even if the
    // reference is not overflowing as well (e.g. virtual elements with no
    // width or height)

    var arrowLen = within(0, referenceRect[len], arrowRect[len]);
    var minOffset = isBasePlacement ? referenceRect[len] / 2 - additive - arrowLen - arrowPaddingMin - normalizedTetherOffsetValue.mainAxis : minLen - arrowLen - arrowPaddingMin - normalizedTetherOffsetValue.mainAxis;
    var maxOffset = isBasePlacement ? -referenceRect[len] / 2 + additive + arrowLen + arrowPaddingMax + normalizedTetherOffsetValue.mainAxis : maxLen + arrowLen + arrowPaddingMax + normalizedTetherOffsetValue.mainAxis;
    var arrowOffsetParent = state.elements.arrow && getOffsetParent(state.elements.arrow);
    var clientOffset = arrowOffsetParent ? mainAxis === 'y' ? arrowOffsetParent.clientTop || 0 : arrowOffsetParent.clientLeft || 0 : 0;
    var offsetModifierValue = (_offsetModifierState$ = offsetModifierState == null ? void 0 : offsetModifierState[mainAxis]) != null ? _offsetModifierState$ : 0;
    var tetherMin = offset + minOffset - offsetModifierValue - clientOffset;
    var tetherMax = offset + maxOffset - offsetModifierValue;
    var preventedOffset = within(tether ? min(min$1, tetherMin) : min$1, offset, tether ? max(max$1, tetherMax) : max$1);
    popperOffsets[mainAxis] = preventedOffset;
    data[mainAxis] = preventedOffset - offset;
  }

  if (checkAltAxis) {
    var _offsetModifierState$2;

    var _mainSide = mainAxis === 'x' ? top : left;

    var _altSide = mainAxis === 'x' ? bottom : right;

    var _offset = popperOffsets[altAxis];

    var _len = altAxis === 'y' ? 'height' : 'width';

    var _min = _offset + overflow[_mainSide];

    var _max = _offset - overflow[_altSide];

    var isOriginSide = [top, left].indexOf(basePlacement) !== -1;

    var _offsetModifierValue = (_offsetModifierState$2 = offsetModifierState == null ? void 0 : offsetModifierState[altAxis]) != null ? _offsetModifierState$2 : 0;

    var _tetherMin = isOriginSide ? _min : _offset - referenceRect[_len] - popperRect[_len] - _offsetModifierValue + normalizedTetherOffsetValue.altAxis;

    var _tetherMax = isOriginSide ? _offset + referenceRect[_len] + popperRect[_len] - _offsetModifierValue - normalizedTetherOffsetValue.altAxis : _max;

    var _preventedOffset = tether && isOriginSide ? withinMaxClamp(_tetherMin, _offset, _tetherMax) : within(tether ? _tetherMin : _min, _offset, tether ? _tetherMax : _max);

    popperOffsets[altAxis] = _preventedOffset;
    data[altAxis] = _preventedOffset - _offset;
  }

  state.modifiersData[name] = data;
} // eslint-disable-next-line import/no-unused-modules


var preventOverflow$1 = {
  name: 'preventOverflow',
  enabled: true,
  phase: 'main',
  fn: preventOverflow,
  requiresIfExists: ['offset']
};

function getHTMLElementScroll(element) {
  return {
    scrollLeft: element.scrollLeft,
    scrollTop: element.scrollTop
  };
}

function getNodeScroll(node) {
  if (node === getWindow(node) || !isHTMLElement(node)) {
    return getWindowScroll(node);
  } else {
    return getHTMLElementScroll(node);
  }
}

function isElementScaled(element) {
  var rect = element.getBoundingClientRect();
  var scaleX = round(rect.width) / element.offsetWidth || 1;
  var scaleY = round(rect.height) / element.offsetHeight || 1;
  return scaleX !== 1 || scaleY !== 1;
} // Returns the composite rect of an element relative to its offsetParent.
// Composite means it takes into account transforms as well as layout.


function getCompositeRect(elementOrVirtualElement, offsetParent, isFixed) {
  if (isFixed === void 0) {
    isFixed = false;
  }

  var isOffsetParentAnElement = isHTMLElement(offsetParent);
  var offsetParentIsScaled = isHTMLElement(offsetParent) && isElementScaled(offsetParent);
  var documentElement = getDocumentElement(offsetParent);
  var rect = getBoundingClientRect(elementOrVirtualElement, offsetParentIsScaled, isFixed);
  var scroll = {
    scrollLeft: 0,
    scrollTop: 0
  };
  var offsets = {
    x: 0,
    y: 0
  };

  if (isOffsetParentAnElement || !isOffsetParentAnElement && !isFixed) {
    if (getNodeName(offsetParent) !== 'body' || // https://github.com/popperjs/popper-core/issues/1078
    isScrollParent(documentElement)) {
      scroll = getNodeScroll(offsetParent);
    }

    if (isHTMLElement(offsetParent)) {
      offsets = getBoundingClientRect(offsetParent, true);
      offsets.x += offsetParent.clientLeft;
      offsets.y += offsetParent.clientTop;
    } else if (documentElement) {
      offsets.x = getWindowScrollBarX(documentElement);
    }
  }

  return {
    x: rect.left + scroll.scrollLeft - offsets.x,
    y: rect.top + scroll.scrollTop - offsets.y,
    width: rect.width,
    height: rect.height
  };
}

function order(modifiers) {
  var map = new Map();
  var visited = new Set();
  var result = [];
  modifiers.forEach(function (modifier) {
    map.set(modifier.name, modifier);
  }); // On visiting object, check for its dependencies and visit them recursively

  function sort(modifier) {
    visited.add(modifier.name);
    var requires = [].concat(modifier.requires || [], modifier.requiresIfExists || []);
    requires.forEach(function (dep) {
      if (!visited.has(dep)) {
        var depModifier = map.get(dep);

        if (depModifier) {
          sort(depModifier);
        }
      }
    });
    result.push(modifier);
  }

  modifiers.forEach(function (modifier) {
    if (!visited.has(modifier.name)) {
      // check for visited object
      sort(modifier);
    }
  });
  return result;
}

function orderModifiers(modifiers) {
  // order based on dependencies
  var orderedModifiers = order(modifiers); // order based on phase

  return modifierPhases.reduce(function (acc, phase) {
    return acc.concat(orderedModifiers.filter(function (modifier) {
      return modifier.phase === phase;
    }));
  }, []);
}

function debounce$1(fn) {
  var pending;
  return function () {
    if (!pending) {
      pending = new Promise(function (resolve) {
        Promise.resolve().then(function () {
          pending = undefined;
          resolve(fn());
        });
      });
    }

    return pending;
  };
}

function mergeByName(modifiers) {
  var merged = modifiers.reduce(function (merged, current) {
    var existing = merged[current.name];
    merged[current.name] = existing ? Object.assign({}, existing, current, {
      options: Object.assign({}, existing.options, current.options),
      data: Object.assign({}, existing.data, current.data)
    }) : current;
    return merged;
  }, {}); // IE11 does not support Object.values

  return Object.keys(merged).map(function (key) {
    return merged[key];
  });
}

var DEFAULT_OPTIONS = {
  placement: 'bottom',
  modifiers: [],
  strategy: 'absolute'
};

function areValidElements() {
  for (var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++) {
    args[_key] = arguments[_key];
  }

  return !args.some(function (element) {
    return !(element && typeof element.getBoundingClientRect === 'function');
  });
}

function popperGenerator(generatorOptions) {
  if (generatorOptions === void 0) {
    generatorOptions = {};
  }

  var _generatorOptions = generatorOptions,
      _generatorOptions$def = _generatorOptions.defaultModifiers,
      defaultModifiers = _generatorOptions$def === void 0 ? [] : _generatorOptions$def,
      _generatorOptions$def2 = _generatorOptions.defaultOptions,
      defaultOptions = _generatorOptions$def2 === void 0 ? DEFAULT_OPTIONS : _generatorOptions$def2;
  return function createPopper(reference, popper, options) {
    if (options === void 0) {
      options = defaultOptions;
    }

    var state = {
      placement: 'bottom',
      orderedModifiers: [],
      options: Object.assign({}, DEFAULT_OPTIONS, defaultOptions),
      modifiersData: {},
      elements: {
        reference: reference,
        popper: popper
      },
      attributes: {},
      styles: {}
    };
    var effectCleanupFns = [];
    var isDestroyed = false;
    var instance = {
      state: state,
      setOptions: function setOptions(setOptionsAction) {
        var options = typeof setOptionsAction === 'function' ? setOptionsAction(state.options) : setOptionsAction;
        cleanupModifierEffects();
        state.options = Object.assign({}, defaultOptions, state.options, options);
        state.scrollParents = {
          reference: isElement$1(reference) ? listScrollParents(reference) : reference.contextElement ? listScrollParents(reference.contextElement) : [],
          popper: listScrollParents(popper)
        }; // Orders the modifiers based on their dependencies and `phase`
        // properties

        var orderedModifiers = orderModifiers(mergeByName([].concat(defaultModifiers, state.options.modifiers))); // Strip out disabled modifiers

        state.orderedModifiers = orderedModifiers.filter(function (m) {
          return m.enabled;
        }); // Validate the provided modifiers so that the consumer will get warned

        runModifierEffects();
        return instance.update();
      },
      // Sync update – it will always be executed, even if not necessary. This
      // is useful for low frequency updates where sync behavior simplifies the
      // logic.
      // For high frequency updates (e.g. `resize` and `scroll` events), always
      // prefer the async Popper#update method
      forceUpdate: function forceUpdate() {
        if (isDestroyed) {
          return;
        }

        var _state$elements = state.elements,
            reference = _state$elements.reference,
            popper = _state$elements.popper; // Don't proceed if `reference` or `popper` are not valid elements
        // anymore

        if (!areValidElements(reference, popper)) {

          return;
        } // Store the reference and popper rects to be read by modifiers


        state.rects = {
          reference: getCompositeRect(reference, getOffsetParent(popper), state.options.strategy === 'fixed'),
          popper: getLayoutRect(popper)
        }; // Modifiers have the ability to reset the current update cycle. The
        // most common use case for this is the `flip` modifier changing the
        // placement, which then needs to re-run all the modifiers, because the
        // logic was previously ran for the previous placement and is therefore
        // stale/incorrect

        state.reset = false;
        state.placement = state.options.placement; // On each update cycle, the `modifiersData` property for each modifier
        // is filled with the initial data specified by the modifier. This means
        // it doesn't persist and is fresh on each update.
        // To ensure persistent data, use `${name}#persistent`

        state.orderedModifiers.forEach(function (modifier) {
          return state.modifiersData[modifier.name] = Object.assign({}, modifier.data);
        });

        for (var index = 0; index < state.orderedModifiers.length; index++) {

          if (state.reset === true) {
            state.reset = false;
            index = -1;
            continue;
          }

          var _state$orderedModifie = state.orderedModifiers[index],
              fn = _state$orderedModifie.fn,
              _state$orderedModifie2 = _state$orderedModifie.options,
              _options = _state$orderedModifie2 === void 0 ? {} : _state$orderedModifie2,
              name = _state$orderedModifie.name;

          if (typeof fn === 'function') {
            state = fn({
              state: state,
              options: _options,
              name: name,
              instance: instance
            }) || state;
          }
        }
      },
      // Async and optimistically optimized update – it will not be executed if
      // not necessary (debounced to run at most once-per-tick)
      update: debounce$1(function () {
        return new Promise(function (resolve) {
          instance.forceUpdate();
          resolve(state);
        });
      }),
      destroy: function destroy() {
        cleanupModifierEffects();
        isDestroyed = true;
      }
    };

    if (!areValidElements(reference, popper)) {

      return instance;
    }

    instance.setOptions(options).then(function (state) {
      if (!isDestroyed && options.onFirstUpdate) {
        options.onFirstUpdate(state);
      }
    }); // Modifiers have the ability to execute arbitrary code before the first
    // update cycle runs. They will be executed in the same order as the update
    // cycle. This is useful when a modifier adds some persistent data that
    // other modifiers need to use, but the modifier is run after the dependent
    // one.

    function runModifierEffects() {
      state.orderedModifiers.forEach(function (_ref3) {
        var name = _ref3.name,
            _ref3$options = _ref3.options,
            options = _ref3$options === void 0 ? {} : _ref3$options,
            effect = _ref3.effect;

        if (typeof effect === 'function') {
          var cleanupFn = effect({
            state: state,
            name: name,
            instance: instance,
            options: options
          });

          var noopFn = function noopFn() {};

          effectCleanupFns.push(cleanupFn || noopFn);
        }
      });
    }

    function cleanupModifierEffects() {
      effectCleanupFns.forEach(function (fn) {
        return fn();
      });
      effectCleanupFns = [];
    }

    return instance;
  };
}

var defaultModifiers = [eventListeners, popperOffsets$1, computeStyles$1, applyStyles$1, offset$1, flip$1, preventOverflow$1, arrow$1, hide$1];
var createPopper = /*#__PURE__*/popperGenerator({
  defaultModifiers: defaultModifiers
}); // eslint-disable-next-line import/no-unused-modules

/**!
* tippy.js v6.3.7
* (c) 2017-2021 atomiks
* MIT License
*/
var BOX_CLASS = "tippy-box";
var CONTENT_CLASS = "tippy-content";
var BACKDROP_CLASS = "tippy-backdrop";
var ARROW_CLASS = "tippy-arrow";
var SVG_ARROW_CLASS = "tippy-svg-arrow";
var TOUCH_OPTIONS = {
  passive: true,
  capture: true
};
var TIPPY_DEFAULT_APPEND_TO = function TIPPY_DEFAULT_APPEND_TO() {
  return document.body;
};
function getValueAtIndexOrReturn(value, index, defaultValue) {
  if (Array.isArray(value)) {
    var v = value[index];
    return v == null ? Array.isArray(defaultValue) ? defaultValue[index] : defaultValue : v;
  }

  return value;
}
function isType(value, type) {
  var str = {}.toString.call(value);
  return str.indexOf('[object') === 0 && str.indexOf(type + "]") > -1;
}
function invokeWithArgsOrReturn(value, args) {
  return typeof value === 'function' ? value.apply(void 0, args) : value;
}
function debounce(fn, ms) {
  // Avoid wrapping in `setTimeout` if ms is 0 anyway
  if (ms === 0) {
    return fn;
  }

  var timeout;
  return function (arg) {
    clearTimeout(timeout);
    timeout = setTimeout(function () {
      fn(arg);
    }, ms);
  };
}
function splitBySpaces(value) {
  return value.split(/\s+/).filter(Boolean);
}
function normalizeToArray(value) {
  return [].concat(value);
}
function pushIfUnique(arr, value) {
  if (arr.indexOf(value) === -1) {
    arr.push(value);
  }
}
function unique(arr) {
  return arr.filter(function (item, index) {
    return arr.indexOf(item) === index;
  });
}
function getBasePlacement(placement) {
  return placement.split('-')[0];
}
function arrayFrom(value) {
  return [].slice.call(value);
}
function removeUndefinedProps(obj) {
  return Object.keys(obj).reduce(function (acc, key) {
    if (obj[key] !== undefined) {
      acc[key] = obj[key];
    }

    return acc;
  }, {});
}

function div() {
  return document.createElement('div');
}
function isElement(value) {
  return ['Element', 'Fragment'].some(function (type) {
    return isType(value, type);
  });
}
function isNodeList(value) {
  return isType(value, 'NodeList');
}
function isMouseEvent(value) {
  return isType(value, 'MouseEvent');
}
function isReferenceElement(value) {
  return !!(value && value._tippy && value._tippy.reference === value);
}
function getArrayOfElements(value) {
  if (isElement(value)) {
    return [value];
  }

  if (isNodeList(value)) {
    return arrayFrom(value);
  }

  if (Array.isArray(value)) {
    return value;
  }

  return arrayFrom(document.querySelectorAll(value));
}
function setTransitionDuration(els, value) {
  els.forEach(function (el) {
    if (el) {
      el.style.transitionDuration = value + "ms";
    }
  });
}
function setVisibilityState(els, state) {
  els.forEach(function (el) {
    if (el) {
      el.setAttribute('data-state', state);
    }
  });
}
function getOwnerDocument(elementOrElements) {
  var _element$ownerDocumen;

  var _normalizeToArray = normalizeToArray(elementOrElements),
      element = _normalizeToArray[0]; // Elements created via a <template> have an ownerDocument with no reference to the body


  return element != null && (_element$ownerDocumen = element.ownerDocument) != null && _element$ownerDocumen.body ? element.ownerDocument : document;
}
function isCursorOutsideInteractiveBorder(popperTreeData, event) {
  var clientX = event.clientX,
      clientY = event.clientY;
  return popperTreeData.every(function (_ref) {
    var popperRect = _ref.popperRect,
        popperState = _ref.popperState,
        props = _ref.props;
    var interactiveBorder = props.interactiveBorder;
    var basePlacement = getBasePlacement(popperState.placement);
    var offsetData = popperState.modifiersData.offset;

    if (!offsetData) {
      return true;
    }

    var topDistance = basePlacement === 'bottom' ? offsetData.top.y : 0;
    var bottomDistance = basePlacement === 'top' ? offsetData.bottom.y : 0;
    var leftDistance = basePlacement === 'right' ? offsetData.left.x : 0;
    var rightDistance = basePlacement === 'left' ? offsetData.right.x : 0;
    var exceedsTop = popperRect.top - clientY + topDistance > interactiveBorder;
    var exceedsBottom = clientY - popperRect.bottom - bottomDistance > interactiveBorder;
    var exceedsLeft = popperRect.left - clientX + leftDistance > interactiveBorder;
    var exceedsRight = clientX - popperRect.right - rightDistance > interactiveBorder;
    return exceedsTop || exceedsBottom || exceedsLeft || exceedsRight;
  });
}
function updateTransitionEndListener(box, action, listener) {
  var method = action + "EventListener"; // some browsers apparently support `transition` (unprefixed) but only fire
  // `webkitTransitionEnd`...

  ['transitionend', 'webkitTransitionEnd'].forEach(function (event) {
    box[method](event, listener);
  });
}
/**
 * Compared to xxx.contains, this function works for dom structures with shadow
 * dom
 */

function actualContains(parent, child) {
  var target = child;

  while (target) {
    var _target$getRootNode;

    if (parent.contains(target)) {
      return true;
    }

    target = target.getRootNode == null ? void 0 : (_target$getRootNode = target.getRootNode()) == null ? void 0 : _target$getRootNode.host;
  }

  return false;
}

var currentInput = {
  isTouch: false
};
var lastMouseMoveTime = 0;
/**
 * When a `touchstart` event is fired, it's assumed the user is using touch
 * input. We'll bind a `mousemove` event listener to listen for mouse input in
 * the future. This way, the `isTouch` property is fully dynamic and will handle
 * hybrid devices that use a mix of touch + mouse input.
 */

function onDocumentTouchStart() {
  if (currentInput.isTouch) {
    return;
  }

  currentInput.isTouch = true;

  if (window.performance) {
    document.addEventListener('mousemove', onDocumentMouseMove);
  }
}
/**
 * When two `mousemove` event are fired consecutively within 20ms, it's assumed
 * the user is using mouse input again. `mousemove` can fire on touch devices as
 * well, but very rarely that quickly.
 */

function onDocumentMouseMove() {
  var now = performance.now();

  if (now - lastMouseMoveTime < 20) {
    currentInput.isTouch = false;
    document.removeEventListener('mousemove', onDocumentMouseMove);
  }

  lastMouseMoveTime = now;
}
/**
 * When an element is in focus and has a tippy, leaving the tab/window and
 * returning causes it to show again. For mouse users this is unexpected, but
 * for keyboard use it makes sense.
 * TODO: find a better technique to solve this problem
 */

function onWindowBlur() {
  var activeElement = document.activeElement;

  if (isReferenceElement(activeElement)) {
    var instance = activeElement._tippy;

    if (activeElement.blur && !instance.state.isVisible) {
      activeElement.blur();
    }
  }
}
function bindGlobalEventListeners() {
  document.addEventListener('touchstart', onDocumentTouchStart, TOUCH_OPTIONS);
  window.addEventListener('blur', onWindowBlur);
}

var isBrowser = typeof window !== 'undefined' && typeof document !== 'undefined';
var isIE11 = isBrowser ? // @ts-ignore
!!window.msCrypto : false;

var pluginProps = {
  animateFill: false,
  followCursor: false,
  inlinePositioning: false,
  sticky: false
};
var renderProps = {
  allowHTML: false,
  animation: 'fade',
  arrow: true,
  content: '',
  inertia: false,
  maxWidth: 350,
  role: 'tooltip',
  theme: '',
  zIndex: 9999
};
var defaultProps = Object.assign({
  appendTo: TIPPY_DEFAULT_APPEND_TO,
  aria: {
    content: 'auto',
    expanded: 'auto'
  },
  delay: 0,
  duration: [300, 250],
  getReferenceClientRect: null,
  hideOnClick: true,
  ignoreAttributes: false,
  interactive: false,
  interactiveBorder: 2,
  interactiveDebounce: 0,
  moveTransition: '',
  offset: [0, 10],
  onAfterUpdate: function onAfterUpdate() {},
  onBeforeUpdate: function onBeforeUpdate() {},
  onCreate: function onCreate() {},
  onDestroy: function onDestroy() {},
  onHidden: function onHidden() {},
  onHide: function onHide() {},
  onMount: function onMount() {},
  onShow: function onShow() {},
  onShown: function onShown() {},
  onTrigger: function onTrigger() {},
  onUntrigger: function onUntrigger() {},
  onClickOutside: function onClickOutside() {},
  placement: 'top',
  plugins: [],
  popperOptions: {},
  render: null,
  showOnCreate: false,
  touch: true,
  trigger: 'mouseenter focus',
  triggerTarget: null
}, pluginProps, renderProps);
var defaultKeys = Object.keys(defaultProps);
var setDefaultProps = function setDefaultProps(partialProps) {

  var keys = Object.keys(partialProps);
  keys.forEach(function (key) {
    defaultProps[key] = partialProps[key];
  });
};
function getExtendedPassedProps(passedProps) {
  var plugins = passedProps.plugins || [];
  var pluginProps = plugins.reduce(function (acc, plugin) {
    var name = plugin.name,
        defaultValue = plugin.defaultValue;

    if (name) {
      var _name;

      acc[name] = passedProps[name] !== undefined ? passedProps[name] : (_name = defaultProps[name]) != null ? _name : defaultValue;
    }

    return acc;
  }, {});
  return Object.assign({}, passedProps, pluginProps);
}
function getDataAttributeProps(reference, plugins) {
  var propKeys = plugins ? Object.keys(getExtendedPassedProps(Object.assign({}, defaultProps, {
    plugins: plugins
  }))) : defaultKeys;
  var props = propKeys.reduce(function (acc, key) {
    var valueAsString = (reference.getAttribute("data-tippy-" + key) || '').trim();

    if (!valueAsString) {
      return acc;
    }

    if (key === 'content') {
      acc[key] = valueAsString;
    } else {
      try {
        acc[key] = JSON.parse(valueAsString);
      } catch (e) {
        acc[key] = valueAsString;
      }
    }

    return acc;
  }, {});
  return props;
}
function evaluateProps(reference, props) {
  var out = Object.assign({}, props, {
    content: invokeWithArgsOrReturn(props.content, [reference])
  }, props.ignoreAttributes ? {} : getDataAttributeProps(reference, props.plugins));
  out.aria = Object.assign({}, defaultProps.aria, out.aria);
  out.aria = {
    expanded: out.aria.expanded === 'auto' ? props.interactive : out.aria.expanded,
    content: out.aria.content === 'auto' ? props.interactive ? null : 'describedby' : out.aria.content
  };
  return out;
}

var innerHTML = function innerHTML() {
  return 'innerHTML';
};

function dangerouslySetInnerHTML(element, html) {
  element[innerHTML()] = html;
}

function createArrowElement(value) {
  var arrow = div();

  if (value === true) {
    arrow.className = ARROW_CLASS;
  } else {
    arrow.className = SVG_ARROW_CLASS;

    if (isElement(value)) {
      arrow.appendChild(value);
    } else {
      dangerouslySetInnerHTML(arrow, value);
    }
  }

  return arrow;
}

function setContent(content, props) {
  if (isElement(props.content)) {
    dangerouslySetInnerHTML(content, '');
    content.appendChild(props.content);
  } else if (typeof props.content !== 'function') {
    if (props.allowHTML) {
      dangerouslySetInnerHTML(content, props.content);
    } else {
      content.textContent = props.content;
    }
  }
}
function getChildren(popper) {
  var box = popper.firstElementChild;
  var boxChildren = arrayFrom(box.children);
  return {
    box: box,
    content: boxChildren.find(function (node) {
      return node.classList.contains(CONTENT_CLASS);
    }),
    arrow: boxChildren.find(function (node) {
      return node.classList.contains(ARROW_CLASS) || node.classList.contains(SVG_ARROW_CLASS);
    }),
    backdrop: boxChildren.find(function (node) {
      return node.classList.contains(BACKDROP_CLASS);
    })
  };
}
function render(instance) {
  var popper = div();
  var box = div();
  box.className = BOX_CLASS;
  box.setAttribute('data-state', 'hidden');
  box.setAttribute('tabindex', '-1');
  var content = div();
  content.className = CONTENT_CLASS;
  content.setAttribute('data-state', 'hidden');
  setContent(content, instance.props);
  popper.appendChild(box);
  box.appendChild(content);
  onUpdate(instance.props, instance.props);

  function onUpdate(prevProps, nextProps) {
    var _getChildren = getChildren(popper),
        box = _getChildren.box,
        content = _getChildren.content,
        arrow = _getChildren.arrow;

    if (nextProps.theme) {
      box.setAttribute('data-theme', nextProps.theme);
    } else {
      box.removeAttribute('data-theme');
    }

    if (typeof nextProps.animation === 'string') {
      box.setAttribute('data-animation', nextProps.animation);
    } else {
      box.removeAttribute('data-animation');
    }

    if (nextProps.inertia) {
      box.setAttribute('data-inertia', '');
    } else {
      box.removeAttribute('data-inertia');
    }

    box.style.maxWidth = typeof nextProps.maxWidth === 'number' ? nextProps.maxWidth + "px" : nextProps.maxWidth;

    if (nextProps.role) {
      box.setAttribute('role', nextProps.role);
    } else {
      box.removeAttribute('role');
    }

    if (prevProps.content !== nextProps.content || prevProps.allowHTML !== nextProps.allowHTML) {
      setContent(content, instance.props);
    }

    if (nextProps.arrow) {
      if (!arrow) {
        box.appendChild(createArrowElement(nextProps.arrow));
      } else if (prevProps.arrow !== nextProps.arrow) {
        box.removeChild(arrow);
        box.appendChild(createArrowElement(nextProps.arrow));
      }
    } else if (arrow) {
      box.removeChild(arrow);
    }
  }

  return {
    popper: popper,
    onUpdate: onUpdate
  };
} // Runtime check to identify if the render function is the default one; this
// way we can apply default CSS transitions logic and it can be tree-shaken away

render.$$tippy = true;

var idCounter = 1;
var mouseMoveListeners = []; // Used by `hideAll()`

var mountedInstances = [];
function createTippy(reference, passedProps) {
  var props = evaluateProps(reference, Object.assign({}, defaultProps, getExtendedPassedProps(removeUndefinedProps(passedProps)))); // ===========================================================================
  // 🔒 Private members
  // ===========================================================================

  var showTimeout;
  var hideTimeout;
  var scheduleHideAnimationFrame;
  var isVisibleFromClick = false;
  var didHideDueToDocumentMouseDown = false;
  var didTouchMove = false;
  var ignoreOnFirstUpdate = false;
  var lastTriggerEvent;
  var currentTransitionEndListener;
  var onFirstUpdate;
  var listeners = [];
  var debouncedOnMouseMove = debounce(onMouseMove, props.interactiveDebounce);
  var currentTarget; // ===========================================================================
  // 🔑 Public members
  // ===========================================================================

  var id = idCounter++;
  var popperInstance = null;
  var plugins = unique(props.plugins);
  var state = {
    // Is the instance currently enabled?
    isEnabled: true,
    // Is the tippy currently showing and not transitioning out?
    isVisible: false,
    // Has the instance been destroyed?
    isDestroyed: false,
    // Is the tippy currently mounted to the DOM?
    isMounted: false,
    // Has the tippy finished transitioning in?
    isShown: false
  };
  var instance = {
    // properties
    id: id,
    reference: reference,
    popper: div(),
    popperInstance: popperInstance,
    props: props,
    state: state,
    plugins: plugins,
    // methods
    clearDelayTimeouts: clearDelayTimeouts,
    setProps: setProps,
    setContent: setContent,
    show: show,
    hide: hide,
    hideWithInteractivity: hideWithInteractivity,
    enable: enable,
    disable: disable,
    unmount: unmount,
    destroy: destroy
  }; // TODO: Investigate why this early return causes a TDZ error in the tests —
  // it doesn't seem to happen in the browser

  /* istanbul ignore if */

  if (!props.render) {

    return instance;
  } // ===========================================================================
  // Initial mutations
  // ===========================================================================


  var _props$render = props.render(instance),
      popper = _props$render.popper,
      onUpdate = _props$render.onUpdate;

  popper.setAttribute('data-tippy-root', '');
  popper.id = "tippy-" + instance.id;
  instance.popper = popper;
  reference._tippy = instance;
  popper._tippy = instance;
  var pluginsHooks = plugins.map(function (plugin) {
    return plugin.fn(instance);
  });
  var hasAriaExpanded = reference.hasAttribute('aria-expanded');
  addListeners();
  handleAriaExpandedAttribute();
  handleStyles();
  invokeHook('onCreate', [instance]);

  if (props.showOnCreate) {
    scheduleShow();
  } // Prevent a tippy with a delay from hiding if the cursor left then returned
  // before it started hiding


  popper.addEventListener('mouseenter', function () {
    if (instance.props.interactive && instance.state.isVisible) {
      instance.clearDelayTimeouts();
    }
  });
  popper.addEventListener('mouseleave', function () {
    if (instance.props.interactive && instance.props.trigger.indexOf('mouseenter') >= 0) {
      getDocument().addEventListener('mousemove', debouncedOnMouseMove);
    }
  });
  return instance; // ===========================================================================
  // 🔒 Private methods
  // ===========================================================================

  function getNormalizedTouchSettings() {
    var touch = instance.props.touch;
    return Array.isArray(touch) ? touch : [touch, 0];
  }

  function getIsCustomTouchBehavior() {
    return getNormalizedTouchSettings()[0] === 'hold';
  }

  function getIsDefaultRenderFn() {
    var _instance$props$rende;

    // @ts-ignore
    return !!((_instance$props$rende = instance.props.render) != null && _instance$props$rende.$$tippy);
  }

  function getCurrentTarget() {
    return currentTarget || reference;
  }

  function getDocument() {
    var parent = getCurrentTarget().parentNode;
    return parent ? getOwnerDocument(parent) : document;
  }

  function getDefaultTemplateChildren() {
    return getChildren(popper);
  }

  function getDelay(isShow) {
    // For touch or keyboard input, force `0` delay for UX reasons
    // Also if the instance is mounted but not visible (transitioning out),
    // ignore delay
    if (instance.state.isMounted && !instance.state.isVisible || currentInput.isTouch || lastTriggerEvent && lastTriggerEvent.type === 'focus') {
      return 0;
    }

    return getValueAtIndexOrReturn(instance.props.delay, isShow ? 0 : 1, defaultProps.delay);
  }

  function handleStyles(fromHide) {
    if (fromHide === void 0) {
      fromHide = false;
    }

    popper.style.pointerEvents = instance.props.interactive && !fromHide ? '' : 'none';
    popper.style.zIndex = "" + instance.props.zIndex;
  }

  function invokeHook(hook, args, shouldInvokePropsHook) {
    if (shouldInvokePropsHook === void 0) {
      shouldInvokePropsHook = true;
    }

    pluginsHooks.forEach(function (pluginHooks) {
      if (pluginHooks[hook]) {
        pluginHooks[hook].apply(pluginHooks, args);
      }
    });

    if (shouldInvokePropsHook) {
      var _instance$props;

      (_instance$props = instance.props)[hook].apply(_instance$props, args);
    }
  }

  function handleAriaContentAttribute() {
    var aria = instance.props.aria;

    if (!aria.content) {
      return;
    }

    var attr = "aria-" + aria.content;
    var id = popper.id;
    var nodes = normalizeToArray(instance.props.triggerTarget || reference);
    nodes.forEach(function (node) {
      var currentValue = node.getAttribute(attr);

      if (instance.state.isVisible) {
        node.setAttribute(attr, currentValue ? currentValue + " " + id : id);
      } else {
        var nextValue = currentValue && currentValue.replace(id, '').trim();

        if (nextValue) {
          node.setAttribute(attr, nextValue);
        } else {
          node.removeAttribute(attr);
        }
      }
    });
  }

  function handleAriaExpandedAttribute() {
    if (hasAriaExpanded || !instance.props.aria.expanded) {
      return;
    }

    var nodes = normalizeToArray(instance.props.triggerTarget || reference);
    nodes.forEach(function (node) {
      if (instance.props.interactive) {
        node.setAttribute('aria-expanded', instance.state.isVisible && node === getCurrentTarget() ? 'true' : 'false');
      } else {
        node.removeAttribute('aria-expanded');
      }
    });
  }

  function cleanupInteractiveMouseListeners() {
    getDocument().removeEventListener('mousemove', debouncedOnMouseMove);
    mouseMoveListeners = mouseMoveListeners.filter(function (listener) {
      return listener !== debouncedOnMouseMove;
    });
  }

  function onDocumentPress(event) {
    // Moved finger to scroll instead of an intentional tap outside
    if (currentInput.isTouch) {
      if (didTouchMove || event.type === 'mousedown') {
        return;
      }
    }

    var actualTarget = event.composedPath && event.composedPath()[0] || event.target; // Clicked on interactive popper

    if (instance.props.interactive && actualContains(popper, actualTarget)) {
      return;
    } // Clicked on the event listeners target


    if (normalizeToArray(instance.props.triggerTarget || reference).some(function (el) {
      return actualContains(el, actualTarget);
    })) {
      if (currentInput.isTouch) {
        return;
      }

      if (instance.state.isVisible && instance.props.trigger.indexOf('click') >= 0) {
        return;
      }
    } else {
      invokeHook('onClickOutside', [instance, event]);
    }

    if (instance.props.hideOnClick === true) {
      instance.clearDelayTimeouts();
      instance.hide(); // `mousedown` event is fired right before `focus` if pressing the
      // currentTarget. This lets a tippy with `focus` trigger know that it
      // should not show

      didHideDueToDocumentMouseDown = true;
      setTimeout(function () {
        didHideDueToDocumentMouseDown = false;
      }); // The listener gets added in `scheduleShow()`, but this may be hiding it
      // before it shows, and hide()'s early bail-out behavior can prevent it
      // from being cleaned up

      if (!instance.state.isMounted) {
        removeDocumentPress();
      }
    }
  }

  function onTouchMove() {
    didTouchMove = true;
  }

  function onTouchStart() {
    didTouchMove = false;
  }

  function addDocumentPress() {
    var doc = getDocument();
    doc.addEventListener('mousedown', onDocumentPress, true);
    doc.addEventListener('touchend', onDocumentPress, TOUCH_OPTIONS);
    doc.addEventListener('touchstart', onTouchStart, TOUCH_OPTIONS);
    doc.addEventListener('touchmove', onTouchMove, TOUCH_OPTIONS);
  }

  function removeDocumentPress() {
    var doc = getDocument();
    doc.removeEventListener('mousedown', onDocumentPress, true);
    doc.removeEventListener('touchend', onDocumentPress, TOUCH_OPTIONS);
    doc.removeEventListener('touchstart', onTouchStart, TOUCH_OPTIONS);
    doc.removeEventListener('touchmove', onTouchMove, TOUCH_OPTIONS);
  }

  function onTransitionedOut(duration, callback) {
    onTransitionEnd(duration, function () {
      if (!instance.state.isVisible && popper.parentNode && popper.parentNode.contains(popper)) {
        callback();
      }
    });
  }

  function onTransitionedIn(duration, callback) {
    onTransitionEnd(duration, callback);
  }

  function onTransitionEnd(duration, callback) {
    var box = getDefaultTemplateChildren().box;

    function listener(event) {
      if (event.target === box) {
        updateTransitionEndListener(box, 'remove', listener);
        callback();
      }
    } // Make callback synchronous if duration is 0
    // `transitionend` won't fire otherwise


    if (duration === 0) {
      return callback();
    }

    updateTransitionEndListener(box, 'remove', currentTransitionEndListener);
    updateTransitionEndListener(box, 'add', listener);
    currentTransitionEndListener = listener;
  }

  function on(eventType, handler, options) {
    if (options === void 0) {
      options = false;
    }

    var nodes = normalizeToArray(instance.props.triggerTarget || reference);
    nodes.forEach(function (node) {
      node.addEventListener(eventType, handler, options);
      listeners.push({
        node: node,
        eventType: eventType,
        handler: handler,
        options: options
      });
    });
  }

  function addListeners() {
    if (getIsCustomTouchBehavior()) {
      on('touchstart', onTrigger, {
        passive: true
      });
      on('touchend', onMouseLeave, {
        passive: true
      });
    }

    splitBySpaces(instance.props.trigger).forEach(function (eventType) {
      if (eventType === 'manual') {
        return;
      }

      on(eventType, onTrigger);

      switch (eventType) {
        case 'mouseenter':
          on('mouseleave', onMouseLeave);
          break;

        case 'focus':
          on(isIE11 ? 'focusout' : 'blur', onBlurOrFocusOut);
          break;

        case 'focusin':
          on('focusout', onBlurOrFocusOut);
          break;
      }
    });
  }

  function removeListeners() {
    listeners.forEach(function (_ref) {
      var node = _ref.node,
          eventType = _ref.eventType,
          handler = _ref.handler,
          options = _ref.options;
      node.removeEventListener(eventType, handler, options);
    });
    listeners = [];
  }

  function onTrigger(event) {
    var _lastTriggerEvent;

    var shouldScheduleClickHide = false;

    if (!instance.state.isEnabled || isEventListenerStopped(event) || didHideDueToDocumentMouseDown) {
      return;
    }

    var wasFocused = ((_lastTriggerEvent = lastTriggerEvent) == null ? void 0 : _lastTriggerEvent.type) === 'focus';
    lastTriggerEvent = event;
    currentTarget = event.currentTarget;
    handleAriaExpandedAttribute();

    if (!instance.state.isVisible && isMouseEvent(event)) {
      // If scrolling, `mouseenter` events can be fired if the cursor lands
      // over a new target, but `mousemove` events don't get fired. This
      // causes interactive tooltips to get stuck open until the cursor is
      // moved
      mouseMoveListeners.forEach(function (listener) {
        return listener(event);
      });
    } // Toggle show/hide when clicking click-triggered tooltips


    if (event.type === 'click' && (instance.props.trigger.indexOf('mouseenter') < 0 || isVisibleFromClick) && instance.props.hideOnClick !== false && instance.state.isVisible) {
      shouldScheduleClickHide = true;
    } else {
      scheduleShow(event);
    }

    if (event.type === 'click') {
      isVisibleFromClick = !shouldScheduleClickHide;
    }

    if (shouldScheduleClickHide && !wasFocused) {
      scheduleHide(event);
    }
  }

  function onMouseMove(event) {
    var target = event.target;
    var isCursorOverReferenceOrPopper = getCurrentTarget().contains(target) || popper.contains(target);

    if (event.type === 'mousemove' && isCursorOverReferenceOrPopper) {
      return;
    }

    var popperTreeData = getNestedPopperTree().concat(popper).map(function (popper) {
      var _instance$popperInsta;

      var instance = popper._tippy;
      var state = (_instance$popperInsta = instance.popperInstance) == null ? void 0 : _instance$popperInsta.state;

      if (state) {
        return {
          popperRect: popper.getBoundingClientRect(),
          popperState: state,
          props: props
        };
      }

      return null;
    }).filter(Boolean);

    if (isCursorOutsideInteractiveBorder(popperTreeData, event)) {
      cleanupInteractiveMouseListeners();
      scheduleHide(event);
    }
  }

  function onMouseLeave(event) {
    var shouldBail = isEventListenerStopped(event) || instance.props.trigger.indexOf('click') >= 0 && isVisibleFromClick;

    if (shouldBail) {
      return;
    }

    if (instance.props.interactive) {
      instance.hideWithInteractivity(event);
      return;
    }

    scheduleHide(event);
  }

  function onBlurOrFocusOut(event) {
    if (instance.props.trigger.indexOf('focusin') < 0 && event.target !== getCurrentTarget()) {
      return;
    } // If focus was moved to within the popper


    if (instance.props.interactive && event.relatedTarget && popper.contains(event.relatedTarget)) {
      return;
    }

    scheduleHide(event);
  }

  function isEventListenerStopped(event) {
    return currentInput.isTouch ? getIsCustomTouchBehavior() !== event.type.indexOf('touch') >= 0 : false;
  }

  function createPopperInstance() {
    destroyPopperInstance();
    var _instance$props2 = instance.props,
        popperOptions = _instance$props2.popperOptions,
        placement = _instance$props2.placement,
        offset = _instance$props2.offset,
        getReferenceClientRect = _instance$props2.getReferenceClientRect,
        moveTransition = _instance$props2.moveTransition;
    var arrow = getIsDefaultRenderFn() ? getChildren(popper).arrow : null;
    var computedReference = getReferenceClientRect ? {
      getBoundingClientRect: getReferenceClientRect,
      contextElement: getReferenceClientRect.contextElement || getCurrentTarget()
    } : reference;
    var tippyModifier = {
      name: '$$tippy',
      enabled: true,
      phase: 'beforeWrite',
      requires: ['computeStyles'],
      fn: function fn(_ref2) {
        var state = _ref2.state;

        if (getIsDefaultRenderFn()) {
          var _getDefaultTemplateCh = getDefaultTemplateChildren(),
              box = _getDefaultTemplateCh.box;

          ['placement', 'reference-hidden', 'escaped'].forEach(function (attr) {
            if (attr === 'placement') {
              box.setAttribute('data-placement', state.placement);
            } else {
              if (state.attributes.popper["data-popper-" + attr]) {
                box.setAttribute("data-" + attr, '');
              } else {
                box.removeAttribute("data-" + attr);
              }
            }
          });
          state.attributes.popper = {};
        }
      }
    };
    var modifiers = [{
      name: 'offset',
      options: {
        offset: offset
      }
    }, {
      name: 'preventOverflow',
      options: {
        padding: {
          top: 2,
          bottom: 2,
          left: 5,
          right: 5
        }
      }
    }, {
      name: 'flip',
      options: {
        padding: 5
      }
    }, {
      name: 'computeStyles',
      options: {
        adaptive: !moveTransition
      }
    }, tippyModifier];

    if (getIsDefaultRenderFn() && arrow) {
      modifiers.push({
        name: 'arrow',
        options: {
          element: arrow,
          padding: 3
        }
      });
    }

    modifiers.push.apply(modifiers, (popperOptions == null ? void 0 : popperOptions.modifiers) || []);
    instance.popperInstance = createPopper(computedReference, popper, Object.assign({}, popperOptions, {
      placement: placement,
      onFirstUpdate: onFirstUpdate,
      modifiers: modifiers
    }));
  }

  function destroyPopperInstance() {
    if (instance.popperInstance) {
      instance.popperInstance.destroy();
      instance.popperInstance = null;
    }
  }

  function mount() {
    var appendTo = instance.props.appendTo;
    var parentNode; // By default, we'll append the popper to the triggerTargets's parentNode so
    // it's directly after the reference element so the elements inside the
    // tippy can be tabbed to
    // If there are clipping issues, the user can specify a different appendTo
    // and ensure focus management is handled correctly manually

    var node = getCurrentTarget();

    if (instance.props.interactive && appendTo === TIPPY_DEFAULT_APPEND_TO || appendTo === 'parent') {
      parentNode = node.parentNode;
    } else {
      parentNode = invokeWithArgsOrReturn(appendTo, [node]);
    } // The popper element needs to exist on the DOM before its position can be
    // updated as Popper needs to read its dimensions


    if (!parentNode.contains(popper)) {
      parentNode.appendChild(popper);
    }

    instance.state.isMounted = true;
    createPopperInstance();
  }

  function getNestedPopperTree() {
    return arrayFrom(popper.querySelectorAll('[data-tippy-root]'));
  }

  function scheduleShow(event) {
    instance.clearDelayTimeouts();

    if (event) {
      invokeHook('onTrigger', [instance, event]);
    }

    addDocumentPress();
    var delay = getDelay(true);

    var _getNormalizedTouchSe = getNormalizedTouchSettings(),
        touchValue = _getNormalizedTouchSe[0],
        touchDelay = _getNormalizedTouchSe[1];

    if (currentInput.isTouch && touchValue === 'hold' && touchDelay) {
      delay = touchDelay;
    }

    if (delay) {
      showTimeout = setTimeout(function () {
        instance.show();
      }, delay);
    } else {
      instance.show();
    }
  }

  function scheduleHide(event) {
    instance.clearDelayTimeouts();
    invokeHook('onUntrigger', [instance, event]);

    if (!instance.state.isVisible) {
      removeDocumentPress();
      return;
    } // For interactive tippies, scheduleHide is added to a document.body handler
    // from onMouseLeave so must intercept scheduled hides from mousemove/leave
    // events when trigger contains mouseenter and click, and the tip is
    // currently shown as a result of a click.


    if (instance.props.trigger.indexOf('mouseenter') >= 0 && instance.props.trigger.indexOf('click') >= 0 && ['mouseleave', 'mousemove'].indexOf(event.type) >= 0 && isVisibleFromClick) {
      return;
    }

    var delay = getDelay(false);

    if (delay) {
      hideTimeout = setTimeout(function () {
        if (instance.state.isVisible) {
          instance.hide();
        }
      }, delay);
    } else {
      // Fixes a `transitionend` problem when it fires 1 frame too
      // late sometimes, we don't want hide() to be called.
      scheduleHideAnimationFrame = requestAnimationFrame(function () {
        instance.hide();
      });
    }
  } // ===========================================================================
  // 🔑 Public methods
  // ===========================================================================


  function enable() {
    instance.state.isEnabled = true;
  }

  function disable() {
    // Disabling the instance should also hide it
    // https://github.com/atomiks/tippy.js-react/issues/106
    instance.hide();
    instance.state.isEnabled = false;
  }

  function clearDelayTimeouts() {
    clearTimeout(showTimeout);
    clearTimeout(hideTimeout);
    cancelAnimationFrame(scheduleHideAnimationFrame);
  }

  function setProps(partialProps) {

    if (instance.state.isDestroyed) {
      return;
    }

    invokeHook('onBeforeUpdate', [instance, partialProps]);
    removeListeners();
    var prevProps = instance.props;
    var nextProps = evaluateProps(reference, Object.assign({}, prevProps, removeUndefinedProps(partialProps), {
      ignoreAttributes: true
    }));
    instance.props = nextProps;
    addListeners();

    if (prevProps.interactiveDebounce !== nextProps.interactiveDebounce) {
      cleanupInteractiveMouseListeners();
      debouncedOnMouseMove = debounce(onMouseMove, nextProps.interactiveDebounce);
    } // Ensure stale aria-expanded attributes are removed


    if (prevProps.triggerTarget && !nextProps.triggerTarget) {
      normalizeToArray(prevProps.triggerTarget).forEach(function (node) {
        node.removeAttribute('aria-expanded');
      });
    } else if (nextProps.triggerTarget) {
      reference.removeAttribute('aria-expanded');
    }

    handleAriaExpandedAttribute();
    handleStyles();

    if (onUpdate) {
      onUpdate(prevProps, nextProps);
    }

    if (instance.popperInstance) {
      createPopperInstance(); // Fixes an issue with nested tippies if they are all getting re-rendered,
      // and the nested ones get re-rendered first.
      // https://github.com/atomiks/tippyjs-react/issues/177
      // TODO: find a cleaner / more efficient solution(!)

      getNestedPopperTree().forEach(function (nestedPopper) {
        // React (and other UI libs likely) requires a rAF wrapper as it flushes
        // its work in one
        requestAnimationFrame(nestedPopper._tippy.popperInstance.forceUpdate);
      });
    }

    invokeHook('onAfterUpdate', [instance, partialProps]);
  }

  function setContent(content) {
    instance.setProps({
      content: content
    });
  }

  function show() {


    var isAlreadyVisible = instance.state.isVisible;
    var isDestroyed = instance.state.isDestroyed;
    var isDisabled = !instance.state.isEnabled;
    var isTouchAndTouchDisabled = currentInput.isTouch && !instance.props.touch;
    var duration = getValueAtIndexOrReturn(instance.props.duration, 0, defaultProps.duration);

    if (isAlreadyVisible || isDestroyed || isDisabled || isTouchAndTouchDisabled) {
      return;
    } // Normalize `disabled` behavior across browsers.
    // Firefox allows events on disabled elements, but Chrome doesn't.
    // Using a wrapper element (i.e. <span>) is recommended.


    if (getCurrentTarget().hasAttribute('disabled')) {
      return;
    }

    invokeHook('onShow', [instance], false);

    if (instance.props.onShow(instance) === false) {
      return;
    }

    instance.state.isVisible = true;

    if (getIsDefaultRenderFn()) {
      popper.style.visibility = 'visible';
    }

    handleStyles();
    addDocumentPress();

    if (!instance.state.isMounted) {
      popper.style.transition = 'none';
    } // If flipping to the opposite side after hiding at least once, the
    // animation will use the wrong placement without resetting the duration


    if (getIsDefaultRenderFn()) {
      var _getDefaultTemplateCh2 = getDefaultTemplateChildren(),
          box = _getDefaultTemplateCh2.box,
          content = _getDefaultTemplateCh2.content;

      setTransitionDuration([box, content], 0);
    }

    onFirstUpdate = function onFirstUpdate() {
      var _instance$popperInsta2;

      if (!instance.state.isVisible || ignoreOnFirstUpdate) {
        return;
      }

      ignoreOnFirstUpdate = true; // reflow

      void popper.offsetHeight;
      popper.style.transition = instance.props.moveTransition;

      if (getIsDefaultRenderFn() && instance.props.animation) {
        var _getDefaultTemplateCh3 = getDefaultTemplateChildren(),
            _box = _getDefaultTemplateCh3.box,
            _content = _getDefaultTemplateCh3.content;

        setTransitionDuration([_box, _content], duration);
        setVisibilityState([_box, _content], 'visible');
      }

      handleAriaContentAttribute();
      handleAriaExpandedAttribute();
      pushIfUnique(mountedInstances, instance); // certain modifiers (e.g. `maxSize`) require a second update after the
      // popper has been positioned for the first time

      (_instance$popperInsta2 = instance.popperInstance) == null ? void 0 : _instance$popperInsta2.forceUpdate();
      invokeHook('onMount', [instance]);

      if (instance.props.animation && getIsDefaultRenderFn()) {
        onTransitionedIn(duration, function () {
          instance.state.isShown = true;
          invokeHook('onShown', [instance]);
        });
      }
    };

    mount();
  }

  function hide() {


    var isAlreadyHidden = !instance.state.isVisible;
    var isDestroyed = instance.state.isDestroyed;
    var isDisabled = !instance.state.isEnabled;
    var duration = getValueAtIndexOrReturn(instance.props.duration, 1, defaultProps.duration);

    if (isAlreadyHidden || isDestroyed || isDisabled) {
      return;
    }

    invokeHook('onHide', [instance], false);

    if (instance.props.onHide(instance) === false) {
      return;
    }

    instance.state.isVisible = false;
    instance.state.isShown = false;
    ignoreOnFirstUpdate = false;
    isVisibleFromClick = false;

    if (getIsDefaultRenderFn()) {
      popper.style.visibility = 'hidden';
    }

    cleanupInteractiveMouseListeners();
    removeDocumentPress();
    handleStyles(true);

    if (getIsDefaultRenderFn()) {
      var _getDefaultTemplateCh4 = getDefaultTemplateChildren(),
          box = _getDefaultTemplateCh4.box,
          content = _getDefaultTemplateCh4.content;

      if (instance.props.animation) {
        setTransitionDuration([box, content], duration);
        setVisibilityState([box, content], 'hidden');
      }
    }

    handleAriaContentAttribute();
    handleAriaExpandedAttribute();

    if (instance.props.animation) {
      if (getIsDefaultRenderFn()) {
        onTransitionedOut(duration, instance.unmount);
      }
    } else {
      instance.unmount();
    }
  }

  function hideWithInteractivity(event) {

    getDocument().addEventListener('mousemove', debouncedOnMouseMove);
    pushIfUnique(mouseMoveListeners, debouncedOnMouseMove);
    debouncedOnMouseMove(event);
  }

  function unmount() {

    if (instance.state.isVisible) {
      instance.hide();
    }

    if (!instance.state.isMounted) {
      return;
    }

    destroyPopperInstance(); // If a popper is not interactive, it will be appended outside the popper
    // tree by default. This seems mainly for interactive tippies, but we should
    // find a workaround if possible

    getNestedPopperTree().forEach(function (nestedPopper) {
      nestedPopper._tippy.unmount();
    });

    if (popper.parentNode) {
      popper.parentNode.removeChild(popper);
    }

    mountedInstances = mountedInstances.filter(function (i) {
      return i !== instance;
    });
    instance.state.isMounted = false;
    invokeHook('onHidden', [instance]);
  }

  function destroy() {

    if (instance.state.isDestroyed) {
      return;
    }

    instance.clearDelayTimeouts();
    instance.unmount();
    removeListeners();
    delete reference._tippy;
    instance.state.isDestroyed = true;
    invokeHook('onDestroy', [instance]);
  }
}

function tippy(targets, optionalProps) {
  if (optionalProps === void 0) {
    optionalProps = {};
  }

  var plugins = defaultProps.plugins.concat(optionalProps.plugins || []);

  bindGlobalEventListeners();
  var passedProps = Object.assign({}, optionalProps, {
    plugins: plugins
  });
  var elements = getArrayOfElements(targets);

  var instances = elements.reduce(function (acc, reference) {
    var instance = reference && createTippy(reference, passedProps);

    if (instance) {
      acc.push(instance);
    }

    return acc;
  }, []);
  return isElement(targets) ? instances[0] : instances;
}

tippy.defaultProps = defaultProps;
tippy.setDefaultProps = setDefaultProps;
tippy.currentInput = currentInput;

// every time the popper is destroyed (i.e. a new target), removing the styles
// and causing transitions to break for singletons when the console is open, but
// most notably for non-transform styles being used, `gpuAcceleration: false`.

Object.assign({}, applyStyles$1, {
  effect: function effect(_ref) {
    var state = _ref.state;
    var initialStyles = {
      popper: {
        position: state.options.strategy,
        left: '0',
        top: '0',
        margin: '0'
      },
      arrow: {
        position: 'absolute'
      },
      reference: {}
    };
    Object.assign(state.elements.popper.style, initialStyles.popper);
    state.styles = initialStyles;

    if (state.elements.arrow) {
      Object.assign(state.elements.arrow.style, initialStyles.arrow);
    } // intentionally return no cleanup function
    // return () => { ... }

  }
});

tippy.setDefaultProps({
  render: render
});

/*-----------------------------------------------------------------------
* Sa11y, the accessibility quality assurance assistant.
* @version: 2.3.5
* @author: Development led by Adam Chaboryk, CPWA
* @acknowledgements: https://this.netlify.app/acknowledgements/
* @license: https://github.com/ryersondmp/sa11y/blob/master/LICENSE.md
* Copyright (c) 2020 - 2022 Toronto Metropolitan University (formerly Ryerson University).
* The above copyright notice shall be included in all copies or
substantial portions of the Software.
------------------------------------------------------------------------*/

/* Translation object */
const Lang = {
  langStrings: {},
  addI18n(strings) {
    this.langStrings = strings;
  },
  _(string) {
    return this.translate(string);
  },
  sprintf(string, ...args) {
    let transString = this._(string);
    if (args && args.length) {
      args.forEach((arg) => {
        transString = transString.replace(/%\([a-zA-z]+\)/, arg);
      });
    }
    return transString;
  },
  translate(string) {
    return this.langStrings[string] || string;
  },
};

class Sa11yCustomChecks {
  setSa11y(sa11y) {
    this.sa11y = sa11y;
  }

  check() {}
}

class Sa11y {
  constructor(options) {
    const defaultOptions = {
      checkRoot: 'body',
      containerIgnore: '.sa11y-ignore',
      contrastIgnore: '.sr-only',
      outlineIgnore: '',
      headerIgnore: '',
      imageIgnore: '',
      linkIgnore: 'nav *, [role="navigation"] *',
      linkIgnoreSpan: '',
      linksToFlag: '',
      nonConsecutiveHeadingIsError: true,
      flagLongHeadings: true,
      showGoodLinkButton: true,
      detectSPArouting: false,
      doNotRun: '',

      // Readability
      readabilityPlugin: true,
      readabilityRoot: 'body',
      readabilityLang: 'en',
      readabilityIgnore: '',

      // Other plugins
      contrastPlugin: true,
      formLabelsPlugin: true,
      linksAdvancedPlugin: true,
      customChecks: true,

      // QA rulesets
      badLinksQA: true,
      strongItalicsQA: true,
      pdfQA: true,
      langQA: true,
      blockquotesQA: true,
      tablesQA: true,
      allCapsQA: true,
      fakeHeadingsQA: true,
      fakeListQA: true,
      duplicateIdQA: true,
      underlinedTextQA: true,
      pageTitleQA: true,
      subscriptQA: true,

      // Embedded content rulesets
      embeddedContentAll: true,
      embeddedContentAudio: true,
      embeddedContentVideo: true,
      embeddedContentDataViz: true,
      embeddedContentTitles: true,
      embeddedContentGeneral: true,

      // Embedded content
      videoContent: 'youtube.com, vimeo.com, yuja.com, panopto.com',
      audioContent: 'soundcloud.com, simplecast.com, podbean.com, buzzsprout.com, blubrry.com, transistor.fm, fusebox.fm, libsyn.com',
      dataVizContent: 'datastudio.google.com, tableau',
      embeddedContent: '',
    };
    defaultOptions.embeddedContent = `${defaultOptions.videoContent}, ${defaultOptions.audioContent}, ${defaultOptions.dataVizContent}`;

    const option = {
      ...defaultOptions,
      ...options,
    };

    // Global constants for annotations.
    const ERROR = Lang._('ERROR');
    const WARNING = Lang._('WARNING');
    const GOOD = Lang._('GOOD');

    this.initialize = () => {
      // Do not run Sa11y if any supplied elements detected on page.
      const checkRunPrevent = () => {
        const { doNotRun } = option;
        return doNotRun.trim().length > 0 ? document.querySelector(doNotRun) : false;
      };

      // Only call Sa11y once page has loaded.
      const documentLoadingCheck = (callback) => {
        if (document.readyState === 'complete') {
          callback();
        } else {
          window.addEventListener('load', callback);
        }
      };

      if (!checkRunPrevent()) {
        this.globals();
        this.utilities();

        // Once document has fully loaded.
        documentLoadingCheck(() => {
          this.buildSa11yUI();
          this.settingPanelToggles();
          this.mainToggle();
          this.skipToIssueTooltip();
          this.detectPageChanges();

          // Pass Sa11y instance to custom checker
          if (option.customChecks && option.customChecks.setSa11y) {
            option.customChecks.setSa11y(this);
          }

          // Check page once page is done loading.
          document.getElementById('sa11y-toggle').disabled = false;
          if (this.store.getItem('sa11y-remember-panel') === 'Closed' || !this.store.getItem('sa11y-remember-panel')) {
            this.panelActive = true;
            this.checkAll();
          }
        });
      }
    };

    this.buildSa11yUI = () => {
      // Icon on the main toggle.
      const MainToggleIcon = "<svg role='img' focusable='false' width='35px' height='35px' aria-hidden='true' xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'><path fill='#ffffff' d='M256 48c114.953 0 208 93.029 208 208 0 114.953-93.029 208-208 208-114.953 0-208-93.029-208-208 0-114.953 93.029-208 208-208m0-40C119.033 8 8 119.033 8 256s111.033 248 248 248 248-111.033 248-248S392.967 8 256 8zm0 56C149.961 64 64 149.961 64 256s85.961 192 192 192 192-85.961 192-192S362.039 64 256 64zm0 44c19.882 0 36 16.118 36 36s-16.118 36-36 36-36-16.118-36-36 16.118-36 36-36zm117.741 98.023c-28.712 6.779-55.511 12.748-82.14 15.807.851 101.023 12.306 123.052 25.037 155.621 3.617 9.26-.957 19.698-10.217 23.315-9.261 3.617-19.699-.957-23.316-10.217-8.705-22.308-17.086-40.636-22.261-78.549h-9.686c-5.167 37.851-13.534 56.208-22.262 78.549-3.615 9.255-14.05 13.836-23.315 10.217-9.26-3.617-13.834-14.056-10.217-23.315 12.713-32.541 24.185-54.541 25.037-155.621-26.629-3.058-53.428-9.027-82.141-15.807-8.6-2.031-13.926-10.648-11.895-19.249s10.647-13.926 19.249-11.895c96.686 22.829 124.283 22.783 220.775 0 8.599-2.03 17.218 3.294 19.249 11.895 2.029 8.601-3.297 17.219-11.897 19.249z'/></svg>";

      const sa11ycontainer = document.createElement('div');
      sa11ycontainer.setAttribute('id', 'sa11y-container');
      sa11ycontainer.setAttribute('role', 'region');
      sa11ycontainer.setAttribute('lang', Lang._('LANG_CODE'));
      sa11ycontainer.setAttribute('aria-label', Lang._('CONTAINER_LABEL'));

      const loadContrastPreference = this.store.getItem('sa11y-remember-contrast') === 'On';
      const loadLabelsPreference = this.store.getItem('sa11y-remember-labels') === 'On';
      const loadChangeRequestPreference = this.store.getItem('sa11y-remember-links-advanced') === 'On';
      const loadReadabilityPreference = this.store.getItem('sa11y-remember-readability') === 'On';

      sa11ycontainer.innerHTML = `<button type="button" aria-expanded="false" id="sa11y-toggle" aria-describedby="sa11y-notification-badge" aria-label="${Lang._('MAIN_TOGGLE_LABEL')}" disabled>
                    ${MainToggleIcon}
                    <div id="sa11y-notification-badge">
                        <span id="sa11y-notification-count"></span>
                        <span id="sa11y-notification-text" class="sa11y-visually-hidden"></span>
                    </div>
                </button>`
        // Start of main container.
        + '<div id="sa11y-panel">'

        // Page Outline tab.
        + `<div id="sa11y-outline-panel" role="tabpanel" aria-labelledby="sa11y-outline-header">
                <div id="sa11y-outline-header" class="sa11y-header-text">
                    <h2 tabindex="-1">${Lang._('PAGE_OUTLINE')}</h2>
                </div>
                <div id="sa11y-outline-content">
                    <ul id="sa11y-outline-list" tabindex="0" role="list" aria-label="${Lang._('PAGE_OUTLINE')}"></ul>
                </div>`

        // Readability tab.
        + `<div id="sa11y-readability-panel">
                    <div id="sa11y-readability-content">
                        <h2 class="sa11y-header-text-inline">${Lang._('LANG_READABILITY')}</h2>
                        <p id="sa11y-readability-info"></p>
                        <ul id="sa11y-readability-details"></ul>
                    </div>
                </div>
            </div>`// End of Page Outline tab.

        // Settings tab.
        + `<div id="sa11y-settings-panel" role="tabpanel" aria-labelledby="sa11y-settings-header">
                <div id="sa11y-settings-header" class="sa11y-header-text">
                    <h2 tabindex="-1">${Lang._('SETTINGS')}</h2>
                </div>
                <div id="sa11y-settings-content">
                    <ul id="sa11y-settings-options">
                        <li id="sa11y-contrast-li">
                            <label id="sa11y-check-contrast" for="sa11y-contrast-toggle">${Lang._('CONTRAST')}</label>
                            <button id="sa11y-contrast-toggle"
                            aria-labelledby="sa11y-check-contrast"
                            class="sa11y-settings-switch"
                            aria-pressed="${loadContrastPreference ? 'true' : 'false'}">${loadContrastPreference ? Lang._('ON') : Lang._('OFF')}</button></li>
                        <li id="sa11y-form-labels-li">
                            <label id="sa11y-check-labels" for="sa11y-labels-toggle">${Lang._('FORM_LABELS')}</label>
                            <button id="sa11y-labels-toggle" aria-labelledby="sa11y-check-labels" class="sa11y-settings-switch"
                            aria-pressed="${loadLabelsPreference ? 'true' : 'false'}">${loadLabelsPreference ? Lang._('ON') : Lang._('OFF')}</button>
                        </li>
                        <li id="sa11y-links-advanced-li">
                            <label id="check-changerequest" for="sa11y-links-advanced-toggle">${Lang._('LINKS_ADVANCED')} <span class="sa11y-badge">AAA</span></label>
                            <button id="sa11y-links-advanced-toggle" aria-labelledby="check-changerequest" class="sa11y-settings-switch"
                            aria-pressed="${loadChangeRequestPreference ? 'true' : 'false'}">${loadChangeRequestPreference ? Lang._('ON') : Lang._('OFF')}</button>
                        </li>
                        <li id="sa11y-readability-li">
                            <label id="check-readability" for="sa11y-readability-toggle">${Lang._('LANG_READABILITY')} <span class="sa11y-badge">AAA</span></label>
                            <button id="sa11y-readability-toggle" aria-labelledby="check-readability" class="sa11y-settings-switch"
                            aria-pressed="${loadReadabilityPreference ? 'true' : 'false'}">${loadReadabilityPreference ? Lang._('ON') : Lang._('OFF')}</button>
                        </li>
                        <li>
                            <label id="sa11y-dark-mode" for="sa11y-theme-toggle">${Lang._('DARK_MODE')}</label>
                            <button id="sa11y-theme-toggle" aria-labelledby="sa11y-dark-mode" class="sa11y-settings-switch"></button>
                        </li>
                    </ul>
                </div>
            </div>`

          // Console warning messages.
          + `<div id="sa11y-panel-alert">
                <div class="sa11y-header-text">
                    <button id="sa11y-close-alert" class="sa11y-close-btn" aria-label="${Lang._('ALERT_CLOSE')}" aria-describedby="sa11y-alert-heading sa11y-panel-alert-text"></button>
                    <h2 id="sa11y-alert-heading">${Lang._('ALERT_TEXT')}</h2>
                </div>
                <p id="sa11y-panel-alert-text"></p>
                <div id="sa11y-panel-alert-preview"></div>
            </div>`

        // Main panel that conveys state of page.
        + `<div id="sa11y-panel-content">
                <button id="sa11y-cycle-toggle" type="button" aria-label="${Lang._('SHORTCUT_SCREEN_READER')}">
                    <div class="sa11y-panel-icon"></div>
                </button>
                <div id="sa11y-panel-text"><h1 class="sa11y-visually-hidden">${Lang._('PANEL_HEADING')}</h1>
                <p id="sa11y-status" aria-live="polite"></p>
                </div>
            </div>`

        // Show Outline & Show Settings button.
        + `<div id="sa11y-panel-controls" role="tablist" aria-orientation="horizontal">
                <button type="button" role="tab" aria-expanded="false" id="sa11y-outline-toggle" aria-controls="sa11y-outline-panel">
                    ${Lang._('SHOW_OUTLINE')}
                </button>
                <button type="button" role="tab" aria-expanded="false" id="sa11y-settings-toggle" aria-controls="sa11y-settings-panel">
                    ${Lang._('SHOW_SETTINGS')}
                </button>
                <div style="width:40px;"></div>
            </div>`

      // End of main container.
      + '</div>';

      const pagebody = document.getElementsByTagName('BODY')[0];
      pagebody.prepend(sa11ycontainer);
    };

    this.globals = () => {
      // Readability root
      if (!option.readabilityRoot) {
        option.readabilityRoot = option.checkRoot;
      }

      // Supported readability languages. Turn module off if not supported.
      const supportedLang = ['en', 'fr', 'es', 'de', 'nl', 'it', 'sv', 'fi', 'da', 'no', 'nb', 'nn'];
      const pageLang = document.querySelector('html').getAttribute('lang');

      // If lang attribute is missing.
      if (!pageLang) {
        option.readabilityPlugin = false;
      } else {
        const pageLangLowerCase = pageLang.toLowerCase();
        if (!supportedLang.some(($el) => pageLangLowerCase.includes($el))) {
          option.readabilityPlugin = false;
        }
      }

      /* Exclusions */
      // Container ignores apply to self and children.
      if (option.containerIgnore) {
        const containerSelectors = option.containerIgnore.split(',').map(($el) => `${$el} *, ${$el}`);
        option.containerIgnore = `[aria-hidden], [data-tippy-root] *, #sa11y-container *, #wpadminbar *, ${containerSelectors.join(', ')}`;
      } else {
        option.containerIgnore = '[aria-hidden], [data-tippy-root] *, #sa11y-container *, #wpadminbar *';
      }
      this.containerIgnore = option.containerIgnore;

      // Contrast exclusions
      this.contrastIgnore = `${this.containerIgnore}, .sa11y-heading-label, script`;
      if (option.contrastIgnore) {
        this.contrastIgnore = `${option.contrastIgnore}, ${this.contrastIgnore}`;
      }

      // Ignore specific regions for readability module.
      this.readabilityIgnore = `${this.containerIgnore}, nav li, [role="navigation"] li`;
      if (option.readabilityIgnore) {
        this.readabilityIgnore = `${option.readabilityIgnore}, ${this.readabilityIgnore}`;
      }

      // Ignore specific headings
      this.headerIgnore = this.containerIgnore;
      if (option.headerIgnore) {
        this.headerIgnore = `${option.headerIgnore}, ${this.headerIgnore}`;
      }

      // Don't add heading label or include in panel.
      if (option.outlineIgnore) {
        this.outlineIgnore = `${option.outlineIgnore}, #sa11y-container h1, #sa11y-container h2`;
      }

      // Ignore specific images.
      this.imageIgnore = `${this.containerIgnore}, [role='presentation'], [src^='https://trck.youvisit.com']`;
      if (option.imageIgnore) {
        this.imageIgnore = `${option.imageIgnore}, ${this.imageIgnore}`;
      }

      // Ignore specific links
      this.linkIgnore = `${this.containerIgnore}, [aria-hidden="true"], .anchorjs-link`;
      if (option.linkIgnore) {
        this.linkIgnore = `${option.linkIgnore}, ${this.linkIgnore}`;
      }

      // Ignore specific classes within links.
      if (option.linkIgnoreSpan) {
        const linkIgnoreSpanSelectors = option.linkIgnoreSpan.split(',').map(($el) => `${$el} *, ${$el}`);
        option.linkIgnoreSpan = `noscript, ${linkIgnoreSpanSelectors.join(', ')}`;
      } else {
        option.linkIgnoreSpan = 'noscript';
      }

      /* Embedded content sources */
      // Video sources.
      if (option.videoContent) {
        const videoContent = option.videoContent.split(/\s*[\s,]\s*/).map(($el) => `[src*='${$el}']`);
        option.videoContent = `video, ${videoContent.join(', ')}`;
      } else {
        option.videoContent = 'video';
      }

      // Audio sources.
      if (option.audioContent) {
        const audioContent = option.audioContent.split(/\s*[\s,]\s*/).map(($el) => `[src*='${$el}']`);
        option.audioContent = `audio, ${audioContent.join(', ')}`;
      } else {
        option.audioContent = 'audio';
      }

      // Data viz sources.
      if (option.dataVizContent) {
        const dataVizContent = option.dataVizContent.split(/\s*[\s,]\s*/).map(($el) => `[src*='${$el}']`);
        option.dataVizContent = dataVizContent.join(', ');
      } else {
        option.dataVizContent = 'datastudio.google.com, tableau';
      }

      // Embedded content all
      if (option.embeddedContent) {
        const embeddedContent = option.embeddedContent.split(/\s*[\s,]\s*/).map(($el) => `[src*='${$el}']`);
        option.embeddedContent = embeddedContent.join(', ');
      }

      // A11y: Determine scroll behaviour
      let reducedMotion = false;
      if (typeof window.matchMedia === 'function') {
        reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
      }
      this.scrollBehaviour = (!reducedMotion || reducedMotion.matches) ? 'auto' : 'smooth';
    };

    this.mainToggle = () => {
      // Keeps checker active when navigating between pages until it is toggled off.
      const sa11yToggle = document.getElementById('sa11y-toggle');
      sa11yToggle.addEventListener('click', (e) => {
        if (this.store.getItem('sa11y-remember-panel') === 'Opened') {
          this.store.setItem('sa11y-remember-panel', 'Closed');
          sa11yToggle.classList.remove('sa11y-on');
          sa11yToggle.setAttribute('aria-expanded', 'false');
          this.resetAll();
          this.updateBadge();
          e.preventDefault();
        } else {
          this.store.setItem('sa11y-remember-panel', 'Opened');
          sa11yToggle.classList.add('sa11y-on');
          sa11yToggle.setAttribute('aria-expanded', 'true');
          this.checkAll();
          // Don't show badge when panel is opened.
          document.getElementById('sa11y-notification-badge').style.display = 'none';
          e.preventDefault();
        }
      });

      // Remember to leave it open
      if (this.store.getItem('sa11y-remember-panel') === 'Opened') {
        sa11yToggle.classList.add('sa11y-on');
        sa11yToggle.setAttribute('aria-expanded', 'true');
      }

      // Crudely give time to load any other content or slow post-rendered JS, iFrames, etc.
      if (sa11yToggle.classList.contains('sa11y-on')) {
        sa11yToggle.classList.toggle('loading-sa11y');
        sa11yToggle.setAttribute('aria-expanded', 'true');
        setTimeout(this.checkAll, 400);
      }

      document.onkeydown = (e) => {
        const evt = e || window.event;
        if (evt.key === 'Escape' && document.getElementById('sa11y-panel').classList.contains('sa11y-active')) {
          sa11yToggle.setAttribute('aria-expanded', 'false');
          sa11yToggle.classList.remove('sa11y-on');
          sa11yToggle.click();
          this.resetAll();
        }

        // Alt + A to enable accessibility checker.
        if (evt.altKey && evt.code === 'KeyA') {
          sa11yToggle.click();
          sa11yToggle.focus();
          evt.preventDefault();
        }
      };
    };

    // ============================================================
    // Helpers: Sanitize HTML and compute ARIA for hyperlinks
    // ============================================================
    this.utilities = () => {
      this.isElementHidden = ($el) => {
        if ($el.getAttribute('hidden') || ($el.offsetWidth === 0 && $el.offsetHeight === 0)) {
          return true;
        }
        const compStyles = getComputedStyle($el);
        return compStyles.getPropertyValue('display') === 'none';
      };

      // Helper: Escape HTML, encode HTML symbols.
      this.escapeHTML = (text) => {
        const $div = document.createElement('div');
        $div.textContent = text;
        return $div.innerHTML.replaceAll('"', '&quot;').replaceAll("'", '&#039;').replaceAll('`', '&#x60;');
      };

      // Helper: Help clean up HTML characters for tooltips and outline panel.
      this.sanitizeForHTML = (string) => {
        const entityMap = {
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;',
          '/': '&#x2F;',
          '`': '&#x60;',
          '=': '&#x3D;',
        };
        return String(string).replace(/[&<>"'`=/]/g, (s) => entityMap[s]);
      };

      // Helper: Compute alt text on images within a text node.
      this.computeTextNodeWithImage = ($el) => {
        const imgArray = Array.from($el.querySelectorAll('img'));
        let returnText = '';
        // No image, has text.
        if (imgArray.length === 0 && $el.textContent.trim().length > 1) {
          returnText = $el.textContent.trim();
        } else if (imgArray.length && $el.textContent.trim().length === 0) {
          // Has image.
          const imgalt = imgArray[0].getAttribute('alt');
          if (!imgalt || imgalt === ' ' || imgalt === '') {
            returnText = ' ';
          } else if (imgalt !== undefined) {
            returnText = imgalt;
          }
        } else if (imgArray.length && $el.textContent.trim().length) {
          // Has image and text.
          // To-do: This is a hack? Any way to do this better?
          imgArray.forEach((element) => {
            element.insertAdjacentHTML('afterend', ` <span class='sa11y-clone-image-text' aria-hidden='true'>${imgArray[0].getAttribute('alt')}</span>`);
          });
          returnText = $el.textContent.trim();
        }
        return returnText;
      };

      // Utility: https://www.joshwcomeau.com/snippets/javascript/debounce/
      this.debounce = (callback, wait) => {
        let timeoutId = null;
        return (...args) => {
          window.clearTimeout(timeoutId);
          timeoutId = window.setTimeout(() => {
            callback(...args);
          }, wait);
        };
      };

      // Helper: Used to ignore child elements within an anchor.
      this.fnIgnore = (element, selector) => {
        const $clone = element.cloneNode(true);
        const $exclude = Array.from(selector ? $clone.querySelectorAll(selector) : $clone.children);
        $exclude.forEach(($c) => {
          $c.parentElement.removeChild($c);
        });
        return $clone;
      };

      // Helper: Handle ARIA labels for Link Text module.
      this.computeAriaLabel = ($el) => {
        // aria-label
        if ($el.matches('[aria-label]')) {
          return $el.getAttribute('aria-label');
        }
        // aria-labeledby.
        if ($el.matches('[aria-labelledby]')) {
          const target = $el.getAttribute('aria-labelledby').split(/\s+/);
          if (target.length > 0) {
            let returnText = '';
            target.forEach((x) => {
              const targetSelector = document.querySelector(`#${x}`);
              if (targetSelector === null) {
                returnText += ' ';
              } else if (targetSelector.hasAttribute('aria-label')) {
                returnText += `${targetSelector.getAttribute('aria-label')}`;
              } else {
                returnText += `${targetSelector.firstChild.nodeValue} `;
              }
            });
            return returnText;
          }
          return '';
        }
        // Child with aria-label
        if (Array.from($el.children).filter((x) => x.matches('[aria-label]')).length > 0) {
          const child = Array.from($el.childNodes);
          let returnText = '';

          // Process each child within node.
          child.forEach((x) => {
            if (x.nodeType === 1) {
              if (x.ariaLabel === null) {
                returnText += x.innerText;
              } else {
                returnText += x.getAttribute('aria-label');
              }
            } else {
              returnText += x.nodeValue;
            }
          });
          return returnText;
        }
        // Child with aria-labelledby
        if (Array.from($el.children).filter((x) => x.matches('[aria-labelledby]')).length > 0) {
          const child = Array.from($el.childNodes);
          let returnText = '';

          // Process each child within node.
          child.forEach((y) => {
            if (y.nodeType === 8) ; else if (y.nodeType === 3) {
              returnText += y.nodeValue;
            } else {
              const target = y.getAttribute('aria-labelledby').split(/\s+/);
              if (target.length > 0) {
                let returnAria = '';
                target.forEach((z) => {
                  if (document.querySelector(`#${z}`) === null) {
                    returnAria += ' ';
                  } else {
                    returnAria += `${document.querySelector(`#${z}`).firstChild.nodeValue} `;
                  }
                });
                returnText += returnAria;
              }
            }
            return '';
          });
          return returnText;
        }
        return 'noAria';
      };

      // Mini function: Find visibible parent of hidden element.
      this.findVisibleParent = (element, property, value) => {
        let $el = element;
        while ($el !== null) {
          const style = window.getComputedStyle($el);
          const propValue = style.getPropertyValue(property);
          if (propValue === value) {
            return $el;
          }
          $el = $el.parentElement;
        }
        return null;
      };

      // Mini function: Calculate top of element.
      this.offsetTop = ($el) => {
        const rect = $el.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        return {
          top: rect.top + scrollTop,
        };
      };

      // Utility: Custom localStorage utility with fallback to sessionStorage.
      this.store = {
        getItem(key) {
          try {
            if (localStorage.getItem(key) === null) {
              return sessionStorage.getItem(key);
            }
            return localStorage.getItem(key);
          } catch (error) {
            // Cookies totally disabled.
            return false;
          }
        },
        setItem(key, value) {
          try {
            localStorage.setItem(key, value);
          } catch (error) {
            sessionStorage.setItem(key, value);
          }
          return true;
        },
      };

      // Utility: Add & remove pulsing border.
      this.addPulse = ($el) => {
        const border = 'sa11y-pulse-border';
        document.querySelectorAll(`.${border}`).forEach((el) => el.classList.remove(border));
        $el.classList.add(border);
        setTimeout(() => {
          $el.classList.remove(border);
        }, 2500);
      };

      // Utility: Send an alert to main panel.
      this.createAlert = (alertMessage, errorPreview) => {
        const $alertPanel = document.getElementById('sa11y-panel-alert');
        const $alertText = document.getElementById('sa11y-panel-alert-text');
        const $alertPreview = document.getElementById('sa11y-panel-alert-preview');
        const $closeAlertToggle = document.getElementById('sa11y-close-alert');
        const $skipBtn = document.getElementById('sa11y-cycle-toggle');

        $alertPanel.classList.add('sa11y-active');
        $alertText.innerHTML = alertMessage;
        if (errorPreview) {
          $alertPreview.classList.add('sa11y-panel-alert-preview');
          $alertPreview.innerHTML = errorPreview;
        }
        setTimeout(() => {
          $closeAlertToggle.focus();
        }, 500);

        // Closing alert sets focus back to Skip to Issue toggle.
        $closeAlertToggle.addEventListener('click', () => {
          this.removeAlert();
          $skipBtn.focus();
        });
      };

      // Utility: Destory alert.
      this.removeAlert = () => {
        const $alertPanel = document.getElementById('sa11y-panel-alert');
        const $alertText = document.getElementById('sa11y-panel-alert-text');
        const $alertPreview = document.getElementById('sa11y-panel-alert-preview');
        $alertPanel.classList.remove('sa11y-active');
        $alertPreview.classList.remove('sa11y-panel-alert-preview');
        while ($alertText.firstChild) $alertText.removeChild($alertText.firstChild);
        while ($alertPreview.firstChild) $alertPreview.removeChild($alertPreview.firstChild);
      };

      // Utility: Replace newlines and double spaces with a single space.
      this.getText = ($el) => $el.textContent.replace(/[\n\r]+|[\s]{2,}/g, ' ').trim();

      // Utility: Get next sibling.
      this.getNextSibling = (elem, selector) => {
        let sibling = elem.nextElementSibling;
        if (!selector) return sibling;
        while (sibling) {
          if (sibling.matches(selector)) return sibling;
          sibling = sibling.nextElementSibling;
        }
        return '';
      };
    };

    //----------------------------------------------------------------------
    // Setting's panel: Additional ruleset toggles.
    //----------------------------------------------------------------------
    this.settingPanelToggles = () => {
      // Toggle: Contrast
      const $contrastToggle = document.getElementById('sa11y-contrast-toggle');
      $contrastToggle.onclick = async () => {
        if (this.store.getItem('sa11y-remember-contrast') === 'On') {
          this.store.setItem('sa11y-remember-contrast', 'Off');
          $contrastToggle.textContent = `${Lang._('OFF')}`;
          $contrastToggle.setAttribute('aria-pressed', 'false');
          this.resetAll(false);
          await this.checkAll();
        } else {
          this.store.setItem('sa11y-remember-contrast', 'On');
          $contrastToggle.textContent = `${Lang._('ON')}`;
          $contrastToggle.setAttribute('aria-pressed', 'true');
          this.resetAll(false);
          await this.checkAll();
        }
      };

      // Toggle: Form labels
      const $labelsToggle = document.getElementById('sa11y-labels-toggle');
      $labelsToggle.onclick = async () => {
        if (this.store.getItem('sa11y-remember-labels') === 'On') {
          this.store.setItem('sa11y-remember-labels', 'Off');
          $labelsToggle.textContent = `${Lang._('OFF')}`;
          $labelsToggle.setAttribute('aria-pressed', 'false');
          this.resetAll(false);
          await this.checkAll();
        } else {
          this.store.setItem('sa11y-remember-labels', 'On');
          $labelsToggle.textContent = `${Lang._('ON')}`;
          $labelsToggle.setAttribute('aria-pressed', 'true');
          this.resetAll(false);
          await this.checkAll();
        }
      };

      // Toggle: Links (Advanced)
      const $linksToggle = document.getElementById('sa11y-links-advanced-toggle');
      $linksToggle.onclick = async () => {
        if (this.store.getItem('sa11y-remember-links-advanced') === 'On') {
          this.store.setItem('sa11y-remember-links-advanced', 'Off');
          $linksToggle.textContent = `${Lang._('OFF')}`;
          $linksToggle.setAttribute('aria-pressed', 'false');
          this.resetAll(false);
          await this.checkAll();
        } else {
          this.store.setItem('sa11y-remember-links-advanced', 'On');
          $linksToggle.textContent = `${Lang._('ON')}`;
          $linksToggle.setAttribute('aria-pressed', 'true');
          this.resetAll(false);
          await this.checkAll();
        }
      };

      // Toggle: Readability
      const $readabilityToggle = document.getElementById('sa11y-readability-toggle');
      $readabilityToggle.onclick = async () => {
        if (this.store.getItem('sa11y-remember-readability') === 'On') {
          this.store.setItem('sa11y-remember-readability', 'Off');
          $readabilityToggle.textContent = `${Lang._('OFF')}`;
          $readabilityToggle.setAttribute('aria-pressed', 'false');
          document.getElementById('sa11y-readability-panel').classList.remove('sa11y-active');
          this.resetAll(false);
          await this.checkAll();
        } else {
          this.store.setItem('sa11y-remember-readability', 'On');
          $readabilityToggle.textContent = `${Lang._('ON')}`;
          $readabilityToggle.setAttribute('aria-pressed', 'true');
          document.getElementById('sa11y-readability-panel').classList.add('sa11y-active');
          this.resetAll(false);
          await this.checkAll();
        }
      };

      if (this.store.getItem('sa11y-remember-readability') === 'On') {
        document.getElementById('sa11y-readability-panel').classList.add('sa11y-active');
      }

      // Toggle: Dark mode. (Credits: https://derekkedziora.com/blog/dark-mode-revisited)
      const systemInitiatedDark = window.matchMedia('(prefers-color-scheme: dark)');
      const $themeToggle = document.getElementById('sa11y-theme-toggle');
      const html = document.querySelector('html');

      if (systemInitiatedDark.matches) {
        $themeToggle.textContent = `${Lang._('ON')}`;
        $themeToggle.setAttribute('aria-pressed', 'true');
      } else {
        $themeToggle.textContent = `${Lang._('OFF')}`;
        $themeToggle.setAttribute('aria-pressed', 'false');
      }

      const prefersColorTest = () => {
        if (systemInitiatedDark.matches) {
          html.setAttribute('data-sa11y-theme', 'dark');
          $themeToggle.textContent = `${Lang._('ON')}`;
          $themeToggle.setAttribute('aria-pressed', 'true');
          this.store.setItem('sa11y-remember-theme', '');
        } else {
          html.setAttribute('data-sa11y-theme', 'light');
          $themeToggle.textContent = `${Lang._('OFF')}`;
          $themeToggle.setAttribute('aria-pressed', 'false');
          this.store.setItem('sa11y-remember-theme', '');
        }
      };

      systemInitiatedDark.addEventListener('change', prefersColorTest);
      $themeToggle.onclick = async () => {
        const theme = this.store.getItem('sa11y-remember-theme');
        if (theme === 'dark') {
          html.setAttribute('data-sa11y-theme', 'light');
          this.store.setItem('sa11y-remember-theme', 'light');
          $themeToggle.textContent = `${Lang._('OFF')}`;
          $themeToggle.setAttribute('aria-pressed', 'false');
        } else if (theme === 'light') {
          html.setAttribute('data-sa11y-theme', 'dark');
          this.store.setItem('sa11y-remember-theme', 'dark');
          $themeToggle.textContent = `${Lang._('ON')}`;
          $themeToggle.setAttribute('aria-pressed', 'true');
        } else if (systemInitiatedDark.matches) {
          html.setAttribute('data-sa11y-theme', 'light');
          this.store.setItem('sa11y-remember-theme', 'light');
          $themeToggle.textContent = `${Lang._('OFF')}`;
          $themeToggle.setAttribute('aria-pressed', 'false');
        } else {
          html.setAttribute('data-sa11y-theme', 'dark');
          this.store.setItem('sa11y-remember-theme', 'dark');
          $themeToggle.textContent = `${Lang._('ON')}`;
          $themeToggle.setAttribute('aria-pressed', 'true');
        }
      };
      const theme = this.store.getItem('sa11y-remember-theme');
      if (theme === 'dark') {
        html.setAttribute('data-sa11y-theme', 'dark');
        this.store.setItem('sa11y-remember-theme', 'dark');
        $themeToggle.textContent = `${Lang._('ON')}`;
        $themeToggle.setAttribute('aria-pressed', 'true');
      } else if (theme === 'light') {
        html.setAttribute('data-sa11y-theme', 'light');
        this.store.setItem('sa11y-remember-theme', 'light');
        $themeToggle.textContent = `${Lang._('OFF')}`;
        $themeToggle.setAttribute('aria-pressed', 'false');
      }
    };

    //----------------------------------------------------------------------
    // Tooltip for Jump-to-Issue button.
    //----------------------------------------------------------------------
    this.skipToIssueTooltip = () => {
      let keyboardShortcut;
      if (navigator.userAgent.indexOf('Mac') !== -1) {
        keyboardShortcut = '<span class="sa11y-kbd">Option</span> + <span class="sa11y-kbd">S</span>';
      } else {
        keyboardShortcut = '<span class="sa11y-kbd">Alt</span> + <span class="sa11y-kbd">S</span>';
      }

      tippy('#sa11y-cycle-toggle', {
        content: `<div style="text-align:center">${Lang._('SHORTCUT_TOOLTIP')} &raquo;<br>${keyboardShortcut}</div>`,
        allowHTML: true,
        delay: [500, 0],
        trigger: 'mouseenter focusin',
        arrow: true,
        placement: 'top',
        theme: 'sa11y-theme',
        aria: {
          content: null,
          expanded: false,
        },
        appendTo: document.body,
        zIndex: 2147483645,
      });
    };

    //----------------------------------------------------------------------
    // Feature to detect if URL changed for bookmarklet/SPAs.
    //----------------------------------------------------------------------
    this.detectPageChanges = () => {
      // Feature to detect page changes (e.g. SPAs).
      if (option.detectSPArouting === true) {
        let url = window.location.href.split('#')[0];

        const checkURL = this.debounce(async () => {
          if (url !== window.location.href.split('#')[0]) {
            // If panel is closed.
            if (this.store.getItem('sa11y-remember-panel') === 'Closed' || !this.store.getItem('sa11y-remember-panel')) {
              this.panelActive = true;
              this.checkAll();
            }
            // Async scan while panel is open.
            if (this.panelActive === true) {
              this.resetAll(false);
              await this.checkAll();
            }
            // Performance: New URL becomes current.
            url = window.location.href;
          }
        }, 250);
        window.addEventListener('mousemove', checkURL);
        window.addEventListener('keydown', checkURL);
      }
    };

    // ----------------------------------------------------------------------
    // Check all
    // ----------------------------------------------------------------------
    this.checkAll = async () => {
      this.errorCount = 0;
      this.warningCount = 0;

      // Error handling. If specified selector doesn't exist on page, scan the body of page instead.
      const rootTarget = document.querySelector(option.checkRoot);
      if (!rootTarget) {
        this.root = document.querySelector('body');
        this.createAlert(`${Lang.sprintf('ERROR_MISSING_ROOT_TARGET', option.checkRoot)}`);
      } else {
        this.root = document.querySelector(option.checkRoot);
      }

      this.findElements();

      // Ruleset checks
      this.checkHeaders();
      this.checkLinkText();
      this.checkAltText();

      // Contrast plugin
      if (option.contrastPlugin === true) {
        if (this.store.getItem('sa11y-remember-contrast') === 'On') {
          this.checkContrast();
        }
      } else {
        const contrastLi = document.getElementById('sa11y-contrast-li');
        contrastLi.setAttribute('style', 'display: none !important;');
        this.store.setItem('sa11y-remember-contrast', 'Off');
      }

      // Form labels plugin
      if (option.formLabelsPlugin === true) {
        if (this.store.getItem('sa11y-remember-labels') === 'On') {
          this.checkLabels();
        }
      } else {
        const formLabelsLi = document.getElementById('sa11y-form-labels-li');
        formLabelsLi.setAttribute('style', 'display: none !important;');
        this.store.setItem('sa11y-remember-labels', 'Off');
      }

      // Links (Advanced) plugin
      if (option.linksAdvancedPlugin === true) {
        if (this.store.getItem('sa11y-remember-links-advanced') === 'On') {
          this.checkLinksAdvanced();
        }
      } else {
        const linksAdvancedLi = document.getElementById('sa11y-links-advanced-li');
        linksAdvancedLi.setAttribute('style', 'display: none !important;');
        this.store.setItem('sa11y-remember-links-advanced', 'Off');
      }

      // Readability plugin
      if (option.readabilityPlugin === true) {
        if (this.store.getItem('sa11y-remember-readability') === 'On') {
          this.checkReadability();
        }
      } else {
        const readabilityLi = document.getElementById('sa11y-readability-li');
        const readabilityPanel = document.getElementById('sa11y-readability-panel');
        readabilityLi.setAttribute('style', 'display: none !important;');
        readabilityPanel.classList.remove('sa11y-active');
      }

      // Embedded content plugin
      if (option.embeddedContentAll === true) {
        this.checkEmbeddedContent();
      }

      // QA module checks.
      this.checkQA();

      // Custom checks abstracted to seperate class.
      if (option.customChecks && option.customChecks.setSa11y) {
        option.customChecks.check();
      }

      // Update panel
      if (this.panelActive) {
        this.resetAll();
      } else {
        this.updatePanel();
      }
      this.initializeTooltips();
      this.detectOverflow();
      this.nudge();

      // Don't show badge when panel is opened.
      if (!document.getElementsByClassName('sa11y-on').length) {
        this.updateBadge();
      }
    };

    // ============================================================
    // Reset all
    // ============================================================
    this.resetAll = (restartPanel = true) => {
      this.panelActive = false;

      const html = document.querySelector('html');
      html.removeAttribute('data-sa11y-active');

      // Remove eventListeners on the Show Outline and Show Panel toggles.
      const $outlineToggle = document.getElementById('sa11y-outline-toggle');
      const resetOutline = $outlineToggle.cloneNode(true);
      $outlineToggle.parentNode.replaceChild(resetOutline, $outlineToggle);

      const $settingsToggle = document.getElementById('sa11y-settings-toggle');
      const resetSettings = $settingsToggle.cloneNode(true);
      $settingsToggle.parentNode.replaceChild(resetSettings, $settingsToggle);

      // Reset all classes on elements.
      const resetClass = ($el) => {
        $el.forEach((x) => {
          document.querySelectorAll(`.${x}`).forEach((y) => y.classList.remove(x));
        });
      };
      resetClass(['sa11y-error-border', 'sa11y-error-text', 'sa11y-warning-border', 'sa11y-warning-text', 'sa11y-good-border', 'sa11y-good-text', 'sa11y-overflow', 'sa11y-fake-heading']);

      const dataAttr = document.querySelectorAll('[data-sa11y-parent]');
      dataAttr.forEach(($el) => { $el.removeAttribute('data-sa11y-parent'); });

      const allcaps = document.querySelectorAll('.sa11y-warning-uppercase');
      // eslint-disable-next-line no-param-reassign, no-return-assign
      allcaps.forEach(($el) => $el.outerHTML = $el.innerHTML);

      document.getElementById('sa11y-readability-info').innerHTML = '';

      // Remove
      document.querySelectorAll(`
                .sa11y-element,
                .sa11y-instance,
                .sa11y-instance-inline,
                .sa11y-heading-label,
                #sa11y-outline-list li,
                .sa11y-readability-period,
                #sa11y-readability-details li,
                .sa11y-clone-image-text
            `).forEach(($el) => $el.parentNode.removeChild($el));

      // Alert within panel.
      this.removeAlert();

      // Main panel warning and error count.
      const clearStatus = document.querySelector('#sa11y-status');
      while (clearStatus.firstChild) clearStatus.removeChild(clearStatus.firstChild);

      if (restartPanel) {
        document.querySelector('#sa11y-panel').classList.remove('sa11y-active');
      }
    };

    // ============================================================
    // Initialize tooltips for error/warning/pass buttons: (Tippy.js)
    // ============================================================
    this.initializeTooltips = () => {
      tippy('.sa11y-btn', {
        interactive: true,
        trigger: 'mouseenter click focusin', // Focusin trigger to ensure "Jump to issue" button displays tooltip.
        arrow: true,
        delay: [100, 0], // Slight delay to ensure mouse doesn't quickly trigger and hide tooltip.
        theme: 'sa11y-theme',
        placement: 'auto-start',
        allowHTML: true,
        aria: {
          content: 'describedby',
        },
        appendTo: document.body,
        zIndex: 2147483645,
      });
    };

    // ============================================================
    // Detect parent containers that have hidden overflow.
    // ============================================================
    this.detectOverflow = () => {
      const findParentWithOverflow = (element, property, value) => {
        let $el = element;
        while ($el !== null) {
          const style = window.getComputedStyle($el);
          const propValue = style.getPropertyValue(property);
          if (propValue === value) {
            return $el;
          }
          $el = $el.parentElement;
        }
        return null;
      };
      const $findButtons = document.querySelectorAll('.sa11y-btn');
      $findButtons.forEach(($el) => {
        const overflowing = findParentWithOverflow($el, 'overflow', 'hidden');
        if (overflowing !== null) {
          overflowing.classList.add('sa11y-overflow');
        }
      });
    };

    // ============================================================
    // Nudge buttons if they overlap.
    // ============================================================
    this.nudge = () => {
      const sa11yInstance = document.querySelectorAll('.sa11y-instance, .sa11y-instance-inline');
      sa11yInstance.forEach(($el) => {
        const sibling = $el.nextElementSibling;
        if (sibling !== null
          && (sibling.classList.contains('sa11y-instance') || sibling.classList.contains('sa11y-instance-inline'))) {
          sibling.querySelector('button').setAttribute('style', 'margin: -10px -20px !important;');
        }
      });
    };

    // ============================================================
    // Update iOS style notification badge on icon.
    // ============================================================
    this.updateBadge = () => {
      const totalCount = this.errorCount + this.warningCount;
      const notifBadge = document.getElementById('sa11y-notification-badge');
      const notifCount = document.getElementById('sa11y-notification-count');
      const notifText = document.getElementById('sa11y-notification-text');

      if (totalCount === 0) {
        notifBadge.style.display = 'none';
      } else if (this.warningCount > 0 && this.errorCount === 0) {
        notifBadge.style.display = 'flex';
        notifBadge.classList.add('sa11y-notification-badge-warning');
        notifCount.innerText = `${this.warningCount}`;
        notifText.innerText = `${Lang._('PANEL_ICON_WARNINGS')}`;
      } else {
        notifBadge.style.display = 'flex';
        notifBadge.classList.remove('sa11y-notification-badge-warning');
        notifCount.innerText = `${totalCount}`;
        notifText.innerText = Lang._('PANEL_ICON_TOTAL');
      }
    };

    // ----------------------------------------------------------------------
    // Main panel: Display and update panel.
    // ----------------------------------------------------------------------
    this.updatePanel = () => {
      this.panelActive = true;

      this.buildPanel();
      this.skipToIssue();

      const $skipBtn = document.getElementById('sa11y-cycle-toggle');
      $skipBtn.disabled = false;

      const $panel = document.getElementById('sa11y-panel');
      $panel.classList.add('sa11y-active');

      const html = document.querySelector('html');
      html.setAttribute('data-sa11y-active', 'true');

      const $panelContent = document.getElementById('sa11y-panel-content');
      const $status = document.getElementById('sa11y-status');
      const $findButtons = document.querySelectorAll('.sa11y-btn');

      if (this.errorCount > 0 && this.warningCount > 0) {
        $panelContent.setAttribute('class', 'sa11y-errors');
        $status.innerHTML = `${Lang._('ERRORS')} <span class="sa11y-panel-count sa11y-margin-right">${this.errorCount}</span> ${Lang._('WARNINGS')} <span class="sa11y-panel-count">${this.warningCount}</span>`;
      } else if (this.errorCount > 0) {
        $panelContent.setAttribute('class', 'sa11y-errors');
        $status.innerHTML = `${Lang._('ERRORS')} <span class="sa11y-panel-count">${this.errorCount}</span>`;
      } else if (this.warningCount > 0) {
        $panelContent.setAttribute('class', 'sa11y-warnings');
        $status.innerHTML = `${Lang._('WARNINGS')} <span class="sa11y-panel-count">${this.warningCount}</span>`;
      } else {
        $panelContent.setAttribute('class', 'sa11y-good');
        $status.textContent = `${Lang._('PANEL_STATUS_NONE')}`;

        if ($findButtons.length === 0) {
          $skipBtn.disabled = true;
        }
      }
    };

    // ----------------------------------------------------------------------
    // Main panel: Build Show Outline and Settings tabs.
    // ----------------------------------------------------------------------
    this.buildPanel = () => {
      const $outlineToggle = document.getElementById('sa11y-outline-toggle');
      const $outlinePanel = document.getElementById('sa11y-outline-panel');
      const $outlineList = document.getElementById('sa11y-outline-list');
      const $settingsToggle = document.getElementById('sa11y-settings-toggle');
      const $settingsPanel = document.getElementById('sa11y-settings-panel');
      const $settingsContent = document.getElementById('sa11y-settings-content');
      const $headingAnnotations = document.querySelectorAll('.sa11y-heading-label');

      // Show outline panel
      $outlineToggle.addEventListener('click', () => {
        if ($outlineToggle.getAttribute('aria-expanded') === 'true') {
          $outlineToggle.classList.remove('sa11y-outline-active');
          $outlinePanel.classList.remove('sa11y-active');
          $outlineToggle.textContent = `${Lang._('SHOW_OUTLINE')}`;
          $outlineToggle.setAttribute('aria-expanded', 'false');
          this.store.setItem('sa11y-remember-outline', 'Closed');
        } else {
          $outlineToggle.classList.add('sa11y-outline-active');
          $outlinePanel.classList.add('sa11y-active');
          $outlineToggle.textContent = `${Lang._('HIDE_OUTLINE')}`;
          $outlineToggle.setAttribute('aria-expanded', 'true');
          this.store.setItem('sa11y-remember-outline', 'Opened');
        }

        // Set focus on Page Outline heading for accessibility.
        document.querySelector('#sa11y-outline-header > h2').focus();

        // Show heading level annotations.
        $headingAnnotations.forEach(($el) => $el.classList.toggle('sa11y-label-visible'));

        // Close Settings panel when Show Outline is active.
        $settingsPanel.classList.remove('sa11y-active');
        $settingsToggle.classList.remove('sa11y-settings-active');
        $settingsToggle.setAttribute('aria-expanded', 'false');
        $settingsToggle.textContent = `${Lang._('SHOW_SETTINGS')}`;

        // Keyboard accessibility fix for scrollable panel content.
        if ($outlineList.clientHeight > 250) {
          $outlineList.setAttribute('tabindex', '0');
        }
      });

      // Remember to leave outline open
      if (this.store.getItem('sa11y-remember-outline') === 'Opened') {
        $outlineToggle.classList.add('sa11y-outline-active');
        $outlinePanel.classList.add('sa11y-active');
        $outlineToggle.textContent = `${Lang._('HIDE_OUTLINE')}`;
        $outlineToggle.setAttribute('aria-expanded', 'true');
        $headingAnnotations.forEach(($el) => $el.classList.toggle('sa11y-label-visible'));
      }

      // Roving tabindex menu for page outline.
      // Thanks to Srijan for this snippet! https://blog.srij.dev/roving-tabindex-from-scratch
      const children = Array.from($outlineList.querySelectorAll('a'));
      let current = 0;
      const handleKeyDown = (e) => {
        if (!['ArrowUp', 'ArrowDown', 'Space'].includes(e.code)) return;
        if (e.code === 'Space') {
          children[current].click();
          return;
        }
        const selected = children[current];
        selected.setAttribute('tabindex', -1);
        let next;
        if (e.code === 'ArrowDown') {
          next = current + 1;
          if (current === children.length - 1) {
            next = 0;
          }
        } else if ((e.code === 'ArrowUp')) {
          next = current - 1;
          if (current === 0) {
            next = children.length - 1;
          }
        }
        children[next].setAttribute('tabindex', 0);
        children[next].focus();
        current = next;
        e.preventDefault();
      };
      $outlineList.addEventListener('focus', () => {
        if (children.length > 0) {
          $outlineList.setAttribute('tabindex', -1);
          children[current].setAttribute('tabindex', 0);
          children[current].focus();
        }
        $outlineList.addEventListener('keydown', handleKeyDown);
      });
      $outlineList.addEventListener('blur', () => {
        $outlineList.removeEventListener('keydown', handleKeyDown);
      });

      // Show settings panel
      $settingsToggle.addEventListener('click', () => {
        if ($settingsToggle.getAttribute('aria-expanded') === 'true') {
          $settingsToggle.classList.remove('sa11y-settings-active');
          $settingsPanel.classList.remove('sa11y-active');
          $settingsToggle.textContent = `${Lang._('SHOW_SETTINGS')}`;
          $settingsToggle.setAttribute('aria-expanded', 'false');
        } else {
          $settingsToggle.classList.add('sa11y-settings-active');
          $settingsPanel.classList.add('sa11y-active');
          $settingsToggle.textContent = `${Lang._('HIDE_SETTINGS')}`;
          $settingsToggle.setAttribute('aria-expanded', 'true');
        }

        // Set focus on Settings heading for accessibility.
        document.querySelector('#sa11y-settings-header > h2').focus();

        // Close Show Outline panel when Settings is active.
        $outlinePanel.classList.remove('sa11y-active');
        $outlineToggle.classList.remove('sa11y-outline-active');
        $outlineToggle.setAttribute('aria-expanded', 'false');
        $outlineToggle.textContent = `${Lang._('SHOW_OUTLINE')}`;
        $headingAnnotations.forEach(($el) => $el.classList.remove('sa11y-label-visible'));
        this.store.setItem('sa11y-remember-outline', 'Closed');

        // Keyboard accessibility fix for scrollable panel content.
        if ($settingsContent.clientHeight > 350) {
          $settingsContent.setAttribute('tabindex', '0');
          $settingsContent.setAttribute('aria-label', `${Lang._('SETTINGS')}`);
          $settingsContent.setAttribute('role', 'region');
        }
      });

      // Enhanced keyboard accessibility for panel.
      document.getElementById('sa11y-panel-controls').addEventListener('keydown', (e) => {
        const $tab = document.querySelectorAll('#sa11y-outline-toggle[role=tab], #sa11y-settings-toggle[role=tab]');
        if (e.key === 'ArrowRight') {
          for (let i = 0; i < $tab.length; i++) {
            if ($tab[i].getAttribute('aria-expanded') === 'true' || $tab[i].getAttribute('aria-expanded') === 'false') {
              $tab[i + 1].focus();
              e.preventDefault();
              break;
            }
          }
        }
        if (e.key === 'ArrowDown') {
          for (let i = 0; i < $tab.length; i++) {
            if ($tab[i].getAttribute('aria-expanded') === 'true' || $tab[i].getAttribute('aria-expanded') === 'false') {
              $tab[i + 1].focus();
              e.preventDefault();
              break;
            }
          }
        }
        if (e.key === 'ArrowLeft') {
          for (let i = $tab.length - 1; i > 0; i--) {
            if ($tab[i].getAttribute('aria-expanded') === 'true' || $tab[i].getAttribute('aria-expanded') === 'false') {
              $tab[i - 1].focus();
              e.preventDefault();
              break;
            }
          }
        }
        if (e.key === 'ArrowUp') {
          for (let i = $tab.length - 1; i > 0; i--) {
            if ($tab[i].getAttribute('aria-expanded') === 'true' || $tab[i].getAttribute('aria-expanded') === 'false') {
              $tab[i - 1].focus();
              e.preventDefault();
              break;
            }
          }
        }
      });
    };

    // ============================================================
    // Main panel: Skip to issue button.
    // ============================================================

    this.skipToIssue = () => {
      // Constants
      const $findButtons = document.querySelectorAll('[data-sa11y-annotation]');
      const $skipToggle = document.getElementById('sa11y-cycle-toggle');
      const findSa11yBtn = document.querySelectorAll('[data-sa11y-annotation]').length;
      let i = -1;

      // Add pulsing border to visible parent of hidden element.
      const hiddenParent = () => {
        $findButtons.forEach(($el) => {
          const overflowing = this.findVisibleParent($el, 'display', 'none');
          if (overflowing !== null) {
            const hiddenparent = overflowing.previousElementSibling;
            if (hiddenparent) {
              this.addPulse(hiddenparent);
            } else {
              this.addPulse(overflowing.parentNode);
            }
          }
        });
      };

      // Find scroll position.
      const scrollPosition = ($el) => {
        const offsetTopPosition = $el.offsetTop;
        if (offsetTopPosition === 0) {
          const visiblePosition = this.findVisibleParent($el, 'display', 'none');

          // Alert if tooltip is hidden.
          const tooltip = $findButtons[i].getAttribute('data-tippy-content');
          this.createAlert(`${Lang._('NOT_VISIBLE_ALERT')}`, tooltip);

          if (visiblePosition) {
            // Get as close to the hidden parent as possible.
            const prevSibling = visiblePosition.previousElementSibling;
            const { parentNode } = visiblePosition;
            if (prevSibling) {
              return this.offsetTop(prevSibling).top - 150;
            }
            return this.offsetTop(parentNode).top - 150;
          }
        }
        this.removeAlert();
        $skipToggle.focus();
        return this.offsetTop($el).top - 150;
      };

      // Skip to next.
      const next = () => {
        i += 1;
        const $el = $findButtons[i];
        const scrollPos = scrollPosition($el);
        window.scrollTo({
          top: scrollPos,
          behavior: `${this.scrollBehaviour}`,
        });
        if (i >= findSa11yBtn - 1) {
          i = -1;
        }
        hiddenParent();
        $el.focus();
      };

      // Skip to previous.
      const prev = () => {
        i = Math.max(0, i -= 1);
        const $el = $findButtons[i];
        if ($el) {
          const scrollPos = scrollPosition($el);
          window.scrollTo({
            top: scrollPos,
            behavior: `${this.scrollBehaviour}`,
          });
          hiddenParent();
          $el.focus();
        }
      };

      // Jump to issue using keyboard shortcut.
      document.addEventListener('keyup', (e) => {
        e.preventDefault();
        if (findSa11yBtn && (e.altKey && (e.code === 'Period' || e.code === 'KeyS'))) {
          next();
        } else if (findSa11yBtn && (e.altKey && (e.code === 'Comma' || e.code === 'KeyW'))) {
          prev();
        }
      });

      // Jump to issue using click.
      $skipToggle.addEventListener('click', (e) => {
        e.preventDefault();
        next();
      });
    };

    // ============================================================
    // Finds all elements and cache.
    // ============================================================
    this.findElements = () => {
      // Sa11y's panel container
      this.panel = document.getElementById('sa11y-container');

      // Query DOM.
      const find = (selectors, exclude, rootType) => {
        let root;
        if (rootType === 'readability') {
          root = document.querySelector(option.readabilityRoot);
        } else if (rootType === 'document') {
          root = document;
        } else {
          root = document.querySelector(option.checkRoot);
        }
        if (!root) {
          root = document.querySelector('body');
        }
        const exclusions = Array.from(document.querySelectorAll(exclude));
        const queryDOM = Array.from(root.querySelectorAll(selectors));
        const filtered = queryDOM.filter(($el) => !exclusions.includes($el));
        return filtered;
      };

      // Main selectors
      this.contrast = find('*', this.contrastIgnore);
      this.images = find('img', this.imageIgnore);
      this.headings = find('h1, h2, h3, h4, h5, h6, [role="heading"][aria-level]', this.headerIgnore);
      this.headingOne = find('h1, [role="heading"][aria-level="1"]', this.headerIgnore, 'document');
      this.links = find('a[href]', this.linkIgnore);
      this.readability = find('p, li', this.readabilityIgnore, 'readability');

      // Quality assurance module.
      this.language = document.querySelector('html').getAttribute('lang');
      this.paragraphs = find('p', this.containerIgnore);
      this.lists = find('li', this.containerIgnore);
      this.spans = find('span', this.containerIgnore);
      this.blockquotes = find('blockquote', this.containerIgnore);
      this.tables = find('table:not([role="presentation"])', this.containerIgnore);
      this.pdf = find('a[href$=".pdf"]', this.containerIgnore);
      this.strongitalics = find('strong, em', this.containerIgnore);
      this.inputs = find('input, select, textarea', this.containerIgnore);
      this.customErrorLinks = option.linksToFlag ? find(option.linksToFlag, this.containerIgnore) : [];

      // iFrames
      this.iframes = find('iframe, audio, video', this.containerIgnore);
      this.videos = this.iframes.filter(($el) => $el.matches(option.videoContent));
      this.audio = this.iframes.filter(($el) => $el.matches(option.audioContent));
      this.datavisualizations = this.iframes.filter(($el) => $el.matches(option.dataVizContent));
      this.embeddedContent = this.iframes.filter(($el) => !$el.matches(option.embeddedContent));
    };

    //----------------------------------------------------------------------
    // Templating for Error, Warning and Pass buttons.
    //----------------------------------------------------------------------
    this.annotate = (type, content, inline = false) => {
      let message = content;

      const validTypes = [
        ERROR,
        WARNING,
        GOOD,
      ];

      if (validTypes.indexOf(type) === -1) {
        throw Error(`Invalid type [${type}] for annotation`);
      }

      // Update error or warning count.
      [type].forEach(($el) => {
        if ($el === ERROR) {
          this.errorCount += 1;
        } else if ($el === WARNING) {
          this.warningCount += 1;
        }
      });

      const CSSName = {
        [validTypes[0]]: 'error',
        [validTypes[1]]: 'warning',
        [validTypes[2]]: 'good',
      };

      // Make translations easier.
      message = message
        .replaceAll(/<hr>/g, '<hr aria-hidden="true">')
        .replaceAll(/<a[\s]href=/g, '<a target="_blank" rel="noopener noreferrer" href=')
        .replaceAll(/<\/a>/g, `<span class="sa11y-visually-hidden"> (${Lang._('NEW_TAB')})</span></a>`)
        .replaceAll(/{r}/g, 'class="sa11y-red-text"');

      message = this.escapeHTML(message);

      return `<div class=${inline ? 'sa11y-instance-inline' : 'sa11y-instance'}>
                <button data-sa11y-annotation type="button" aria-label="${[type]}" class="sa11y-btn sa11y-${CSSName[type]}-btn${inline ? '-text' : ''}" data-tippy-content="<div lang='${Lang._('LANG_CODE')}'><div class='sa11y-header-text'>${[type]}</div>${message}</div>"></button>
              </div>`;
    };

    //----------------------------------------------------------------------
    // Templating for full-width banners.
    //----------------------------------------------------------------------
    this.annotateBanner = (type, content) => {
      let message = content;

      const validTypes = [
        ERROR,
        WARNING,
        GOOD,
      ];

      if (validTypes.indexOf(type) === -1) {
        throw Error(`Invalid type [${type}] for annotation`);
      }

      const CSSName = {
        [validTypes[0]]: 'error',
        [validTypes[1]]: 'warning',
        [validTypes[2]]: 'good',
      };

      // Update error or warning count.
      [type].forEach(($el) => {
        if ($el === ERROR) {
          this.errorCount += 1;
        } else if ($el === WARNING) {
          this.warningCount += 1;
        }
      });

      // Check if content is a function & make translations easier.
      if (message && {}.toString.call(message) === '[object Function]') {
        message = message
          .replaceAll(/<hr>/g, '<hr aria-hidden="true">')
          .replaceAll(/<a[\s]href=/g, '<a target="_blank" rel="noopener noreferrer" href=')
          .replaceAll(/<\/a>/g, `<span class="sa11y-visually-hidden"> (${Lang._('NEW_TAB')})</span></a>`)
          .replaceAll(/{r}/g, 'class="sa11y-red-text"');
        message = this.escapeHTML(message);
      }

      return `<div class="sa11y-instance sa11y-${CSSName[type]}-message-container"><div role="region" data-sa11y-annotation tabindex="-1" aria-label="${[type]}" class="sa11y-${CSSName[type]}-message" lang="${Lang._('LANG_CODE')}">${message}</div></div>`;
    };

    // ============================================================
    // Rulesets: Check Headings
    // ============================================================
    this.checkHeaders = () => {
      let prevLevel;
      this.headings.forEach(($el, i) => {
        const text = this.computeTextNodeWithImage($el);
        const htext = this.sanitizeForHTML(text);
        let level;

        if ($el.getAttribute('aria-level')) {
          level = +$el.getAttribute('aria-level');
        } else {
          level = +$el.tagName.slice(1);
        }

        const headingLength = $el.textContent.trim().length;
        let error = null;
        let warning = null;

        if (level - prevLevel > 1 && i !== 0) {
          if (option.nonConsecutiveHeadingIsError === true) {
            error = Lang.sprintf('HEADING_NON_CONSECUTIVE_LEVEL', prevLevel, level);
          } else {
            warning = Lang.sprintf('HEADING_NON_CONSECUTIVE_LEVEL', prevLevel, level);
          }
        } else if ($el.textContent.trim().length === 0) {
          if ($el.querySelectorAll('img').length) {
            const imgalt = $el.querySelector('img').getAttribute('alt');
            if (imgalt === null || imgalt === ' ' || imgalt === '') {
              error = Lang.sprintf('HEADING_EMPTY_WITH_IMAGE', level);
              $el.classList.add('sa11y-error-text');
            }
          } else {
            error = Lang.sprintf('HEADING_EMPTY', level);
            $el.classList.add('sa11y-error-text');
          }
        } else if (i === 0 && level !== 1 && level !== 2) {
          error = Lang._('HEADING_FIRST');
        } else if ($el.textContent.trim().length > 170 && option.flagLongHeadings === true) {
          warning = Lang.sprintf('HEADING_LONG', headingLength);
        }

        prevLevel = level;

        // Indicate if heading is totally hidden or visually hidden.
        const headingHidden = this.isElementHidden($el);
        const visibleIcon = (headingHidden === true || ($el.clientHeight === 1 && $el.clientWidth === 1)) ? '<span class="sa11y-hidden-icon"></span><span class="sa11y-visually-hidden">Hidden</span>' : '';
        const visibleStatus = (headingHidden === true || ($el.clientHeight === 1 && $el.clientWidth === 1)) ? 'class="sa11y-hidden-h"' : '';

        // Normal heading.
        const li = `<li class='sa11y-outline-${level}'>
                  <a id="sa11y-link-${i}" tabindex="-1" ${visibleStatus}>
                    <span class='sa11y-badge'>${visibleIcon} ${level}</span>
                    <span class='sa11y-outline-list-item'>${htext}</span>
                  </a>
                </li>`;

        // Error heading.
        const liError = `<li class='sa11y-outline-${level}'>
                  <a id="sa11y-link-${i}" tabindex="-1" ${visibleStatus}>
                    <span class='sa11y-badge sa11y-error-badge'>
                    <span aria-hidden='true'>${visibleIcon} &#33;</span>
                    <span class='sa11y-visually-hidden'>${Lang._('ERROR')}</span> ${level}</span>
                    <span class='sa11y-outline-list-item sa11y-red-text sa11y-bold'>${htext}</span>
                  </a>
                </li>`;

        // Warning heading.
        const liWarning = `<li class='sa11y-outline-${level}'>
                  <a id="sa11y-link-${i}" tabindex="-1" ${visibleStatus}>
                    <span class='sa11y-badge sa11y-warning-badge'>
                    <span aria-hidden='true'>${visibleIcon} &#x3f;</span>
                    <span class='sa11y-visually-hidden'>${Lang._('WARNING')}</span> ${level}</span>
                    <span class='sa11y-outline-list-item sa11y-yellow-text sa11y-bold'>${htext}</span>
                  </a>
                </li>`;

        let ignoreArray = [];
        if (option.outlineIgnore) {
          ignoreArray = Array.from(document.querySelectorAll(this.outlineIgnore));
        }

        const outline = document.querySelector('#sa11y-outline-list');
        if (!ignoreArray.includes($el)) {
          // Append annotations & update panel.
          if (error !== null && $el.closest('a') !== null) {
            $el.classList.add('sa11y-error-border');
            $el.closest('a').insertAdjacentHTML('afterend', this.annotate(ERROR, error, true));
            outline.insertAdjacentHTML('beforeend', liError);
          } else if (error !== null) {
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(ERROR, error));
            outline.insertAdjacentHTML('beforeend', liError);
          } else if (warning !== null && $el.closest('a') !== null) {
            $el.closest('a').insertAdjacentHTML('afterend', this.annotate(WARNING, warning));
            outline.insertAdjacentHTML('beforeend', liWarning);
          } else if (warning !== null) {
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, warning));
            outline.insertAdjacentHTML('beforeend', liWarning);
          } else if (error === null || warning === null) {
            outline.insertAdjacentHTML('beforeend', li);
          }
        }

        const sa11yToggle = document.getElementById('sa11y-toggle');
        if (sa11yToggle.classList.contains('sa11y-on')) {
          // Append heading labels. Although if the heading is in a hidden container, place the anchor just before it's most visible parent.
          const hiddenH = this.findVisibleParent($el, 'display', 'none');
          const plainHeadingLabel = `<span class="sa11y-heading-label">H${level}</span>`;
          const anchor = `<span class="sa11y-element" id="sa11y-h${i}"></span>`;
          if (hiddenH !== null) {
            const hiddenParent = hiddenH.previousElementSibling;
            $el.insertAdjacentHTML('beforeend', plainHeadingLabel);
            if (hiddenParent) {
              hiddenParent.insertAdjacentHTML('beforebegin', anchor);
              hiddenParent.setAttribute('data-sa11y-parent', `h${i}`);
            } else {
              hiddenH.parentNode.insertAdjacentHTML('beforebegin', anchor);
              hiddenH.parentNode.setAttribute('data-sa11y-parent', `h${i}`);
            }
          } else {
            // If the heading isn't hidden, then append id on visible label.
            $el.insertAdjacentHTML('beforeend', `<span id="sa11y-h${i}" class="sa11y-heading-label">H${level}</span>`);
          }

          // Make Page Outline clickable.
          setTimeout(() => {
            const outlineLink = document.getElementById(`sa11y-link-${i}`);
            const alertActive = document.getElementById('sa11y-panel-alert');
            const hID = document.getElementById(`sa11y-h${i}`);
            const hParent = document.querySelector(`[data-sa11y-parent="h${i}"]`);
            const smooth = () => hID.scrollIntoView({ behavior: `${this.scrollBehaviour}`, block: 'center' });
            const pulse = () => ((hParent !== null) ? this.addPulse(hParent) : this.addPulse($el));
            const smoothPulse = (e) => {
              if ((e.type === 'keyup' && e.code === 'Enter') || e.type === 'click') {
                smooth();
                pulse();
                if (outlineLink.classList.contains('sa11y-hidden-h')) {
                  this.createAlert(`${Lang._('HEADING_NOT_VISIBLE_ALERT')}`);
                } else if (alertActive.classList.contains('sa11y-active')) {
                  this.removeAlert();
                }
              }
              e.preventDefault();
            };
            outlineLink.addEventListener('click', smoothPulse, false);
            outlineLink.addEventListener('keyup', smoothPulse, false);
          }, 50);
        }
      });

      // Check to see there is at least one H1 on the page.
      if (this.headingOne.length === 0) {
        const updateH1Outline = `<div class='sa11y-instance sa11y-missing-h1'>
                    <span class='sa11y-badge sa11y-error-badge'><span aria-hidden='true'>!</span><span class='sa11y-visually-hidden'>${Lang._('ERROR')}</span></span>
                    <span class='sa11y-red-text sa11y-bold'>${Lang._('PANEL_HEADING_MISSING_ONE')}</span>
                </div>`;
        document.getElementById('sa11y-outline-header').insertAdjacentHTML('afterend', updateH1Outline);
        this.panel.insertAdjacentHTML('afterend', this.annotateBanner(ERROR, Lang._('HEADING_MISSING_ONE')));
      }
    };

    // ============================================================
    // Rulesets: Link text
    // ============================================================
    this.checkLinkText = () => {
      const containsLinkTextStopWords = (textContent) => {
        const urlText = [
          'http',
          '.asp',
          '.htm',
          '.php',
          '.edu/',
          '.com/',
          '.net/',
          '.org/',
          '.us/',
          '.ca/',
          '.de/',
          '.icu/',
          '.uk/',
          '.ru/',
          '.info/',
          '.top/',
          '.xyz/',
          '.tk/',
          '.cn/',
          '.ga/',
          '.cf/',
          '.nl/',
          '.io/',
          '.fr/',
          '.pe/',
          '.nz/',
          '.pt/',
          '.es/',
          '.pl/',
          '.ua/',
        ];

        const hit = [null, null, null];

        // Flag partial stop words.
        Lang._('PARTIAL_ALT_STOPWORDS').forEach((word) => {
          if (
            textContent.length === word.length && textContent.toLowerCase().indexOf(word) >= 0
          ) {
            hit[0] = word;
          }
          return false;
        });

        // Other warnings we want to add.
        Lang._('WARNING_ALT_STOPWORDS').forEach((word) => {
          if (textContent.toLowerCase().indexOf(word) >= 0) {
            hit[1] = word;
          }
          return false;
        });

        // Flag link text containing URLs.
        urlText.forEach((word) => {
          if (textContent.toLowerCase().indexOf(word) >= 0) {
            hit[2] = word;
          }
          return false;
        });
        return hit;
      };

      this.links.forEach(($el) => {
        let linkText = this.computeAriaLabel($el);
        const hasAriaLabelledBy = $el.getAttribute('aria-labelledby');
        const hasAriaLabel = $el.getAttribute('aria-label');
        let childAriaLabelledBy = null;
        let childAriaLabel = null;
        const hasTitle = $el.getAttribute('title');

        if ($el.children.length) {
          const $firstChild = $el.children[0];
          childAriaLabelledBy = $firstChild.getAttribute('aria-labelledby');
          childAriaLabel = $firstChild.getAttribute('aria-label');
        }

        if (linkText === 'noAria') {
          // Plain text content.
          linkText = this.getText($el);
          const $img = $el.querySelector('img');

          // If an image exists within the link. Help with AccName computation.
          if ($img) {
            // Check if there's aria on the image.
            const imgText = this.computeAriaLabel($img);
            if (imgText !== 'noAria') {
              linkText += imgText;
            } else {
              // No aria? Process alt on image.
              linkText += $img ? ($img.getAttribute('alt') || '') : '';
            }
          }
        }

        const error = containsLinkTextStopWords(this.fnIgnore($el, option.linkIgnoreSpan).textContent.replace(/[!*?↣↳→↓»↴]/g, '').trim());

        if ($el.querySelectorAll('img').length) ; else if ($el.getAttribute('href') && !linkText) {
          // Flag empty hyperlinks.
          if ($el && hasTitle) ; else if ($el.children.length) {
            // Has child elements (e.g. SVG or SPAN) <a><i></i></a>
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang._('LINK_EMPTY_LINK_NO_LABEL'), true));
          } else {
            // Completely empty <a></a>
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang._('LINK_EMPTY'), true));
          }
        } else if (error[0] != null) {
          // Contains stop words.
          if (hasAriaLabelledBy || hasAriaLabel || childAriaLabelledBy || childAriaLabel) {
            if (option.showGoodLinkButton === true) {
              $el.insertAdjacentHTML(
                'beforebegin',
                this.annotate(GOOD, Lang.sprintf('LINK_LABEL', linkText), true),
              );
            }
          } else if ($el.getAttribute('aria-hidden') === 'true' && $el.getAttribute('tabindex') === '-1') ; else {
            $el.classList.add('sa11y-error-text');
            $el.insertAdjacentHTML(
              'afterend',
              this.annotate(ERROR, Lang.sprintf('LINK_STOPWORD', error[0]), true),
            );
          }
        } else if (error[1] != null) {
          // Contains warning words.
          $el.classList.add('sa11y-warning-text');
          $el.insertAdjacentHTML(
            'afterend',
            this.annotate(WARNING, Lang.sprintf('LINK_BEST_PRACTICES', error[1]), true),
          );
        } else if (error[2] != null) {
          // Contains URL in link text.
          if (linkText.length > 40) {
            $el.classList.add('sa11y-warning-text');
            $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang._('LINK_URL'), true));
          }
        } else if (hasAriaLabelledBy || hasAriaLabel || childAriaLabelledBy || childAriaLabel) {
          // If the link has any ARIA, append a "Good" link button.
          if (option.showGoodLinkButton === true) {
            $el.insertAdjacentHTML(
              'beforebegin',
              this.annotate(GOOD, Lang.sprintf('LINK_LABEL', linkText), true),
            );
          }
        }
      });
    };

    // ============================================================
    // Rulesets: Links (Advanced)
    // ============================================================
    this.checkLinksAdvanced = () => {
      const seen = {};
      this.links.forEach(($el) => {
        let linkText = this.computeAriaLabel($el);
        const $img = $el.querySelector('img');

        if (linkText === 'noAria') {
          // Plain text content.
          linkText = this.getText($el);

          // If an image exists within the link.
          if ($img) {
            // Check if there's aria on the image.
            const imgText = this.computeAriaLabel($img);
            if (imgText !== 'noAria') {
              linkText += imgText;
            } else {
              // No aria? Process alt on image.
              linkText += $img ? ($img.getAttribute('alt') || '') : '';
            }
          }
        }

        // Remove whitespace, special characters, etc.
        const linkTextTrimmed = linkText.replace(/'|"|-|\.|\s+/g, '').toLowerCase();

        // Links with identical accessible names have equivalent purpose.
        const href = $el.getAttribute('href');

        if (linkText.length !== 0) {
          if (seen[linkTextTrimmed] && linkTextTrimmed.length !== 0) {
            if (seen[href]) ; else {
              $el.classList.add('sa11y-warning-text');
              $el.insertAdjacentHTML(
                'afterend',
                this.annotate(WARNING, Lang.sprintf('LINK_IDENTICAL_NAME', linkText), true),
              );
            }
          } else {
            seen[linkTextTrimmed] = true;
            seen[href] = true;
          }
        }

        // New tab or new window.
        const containsNewWindowPhrases = Lang._('NEW_WINDOW_PHRASES').some((pass) => {
          if (linkText.trim().length === 0 && !!$el.getAttribute('title')) {
            linkText = $el.getAttribute('title');
          }
          return linkText.toLowerCase().indexOf(pass) >= 0;
        });

        // Link that points to a file type indicates that it does.
        const containsFileTypePhrases = Lang._('FILE_TYPE_PHRASES').some((pass) => linkText.toLowerCase().indexOf(pass) >= 0);

        const fileTypeMatch = $el.matches(`
          a[href$='.pdf'],
          a[href$='.doc'],
          a[href$='.docx'],
          a[href$='.zip'],
          a[href$='.mp3'],
          a[href$='.txt'],
          a[href$='.exe'],
          a[href$='.dmg'],
          a[href$='.rtf'],
          a[href$='.pptx'],
          a[href$='.ppt'],
          a[href$='.xls'],
          a[href$='.xlsx'],
          a[href$='.csv'],
          a[href$='.mp4'],
          a[href$='.mov'],
          a[href$='.avi']
        `);

        if ($el.getAttribute('target') === '_blank' && !fileTypeMatch && !containsNewWindowPhrases) {
          $el.classList.add('sa11y-warning-text');
          $el.insertAdjacentHTML(
            'afterend',
            this.annotate(WARNING, Lang._('NEW_TAB_WARNING'), true),
          );
        }

        if (fileTypeMatch && !containsFileTypePhrases) {
          $el.classList.add('sa11y-warning-text');
          $el.insertAdjacentHTML(
            'beforebegin',
            this.annotate(WARNING, Lang._('FILE_TYPE_WARNING'), true),
          );
        }
      });
    };

    // ============================================================
    // Ruleset: Alternative text
    // ============================================================
    this.checkAltText = () => {
      this.containsAltTextStopWords = (alt) => {
        const altUrl = [
          '.png',
          '.jpg',
          '.jpeg',
          '.webp',
          '.gif',
          '.tiff',
          '.svg',
        ];

        const hit = [null, null, null];
        altUrl.forEach((word) => {
          if (alt.toLowerCase().indexOf(word) >= 0) {
            hit[0] = word;
          }
        });
        Lang._('SUSPICIOUS_ALT_STOPWORDS').forEach((word) => {
          if (alt.toLowerCase().indexOf(word) >= 0) {
            hit[1] = word;
          }
        });
        Lang._('PLACEHOLDER_ALT_STOPWORDS').forEach((word) => {
          if (alt.length === word.length && alt.toLowerCase().indexOf(word) >= 0) {
            hit[2] = word;
          }
        });
        return hit;
      };

      this.images.forEach(($el) => {
        const alt = $el.getAttribute('alt');
        if (alt === null) {
          if ($el.closest('a[href]')) {
            if (this.fnIgnore($el.closest('a[href]'), 'noscript').textContent.trim().length >= 1) {
              $el.classList.add('sa11y-error-border');
              $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('MISSING_ALT_LINK_BUT_HAS_TEXT_MESSAGE')));
            } else if (this.fnIgnore($el.closest('a[href]'), 'noscript').textContent.trim().length === 0) {
              $el.classList.add('sa11y-error-border');
              $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('MISSING_ALT_LINK_MESSAGE')));
            }
          } else {
            // General failure message if image is missing alt.
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('MISSING_ALT_MESSAGE')));
          }
        } else {
          // If alt attribute is present, further tests are done.
          const altText = this.sanitizeForHTML(alt); // Prevent tooltip from breaking.
          const error = this.containsAltTextStopWords(altText);
          const altLength = alt.length;

          if ($el.closest('a[href]') && $el.closest('a[href]').getAttribute('tabindex') === '-1' && $el.closest('a[href]').getAttribute('aria-hidden') === 'true') ; else if (error[0] !== null && $el.closest('a[href]')) {
            // Image fails if a stop word was found.
            $el.classList.add('sa11y-error-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('LINK_IMAGE_BAD_ALT_MESSAGE', error[0], altText)));
          } else if (error[2] !== null && $el.closest('a[href]')) {
            $el.classList.add('sa11y-error-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('LINK_IMAGE_PLACEHOLDER_ALT_MESSAGE', altText)));
          } else if (error[1] !== null && $el.closest('a[href]')) {
            $el.classList.add('sa11y-warning-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('LINK_IMAGE_SUS_ALT_MESSAGE', error[1], altText)));
          } else if (error[0] !== null) {
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('LINK_ALT_HAS_BAD_WORD_MESSAGE', error[0], altText)));
          } else if (error[2] !== null) {
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('ALT_PLACEHOLDER_MESSAGE', altText)));
          } else if (error[1] !== null) {
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('ALT_HAS_SUS_WORD', error[1], altText)));
          } else if ((alt === '' || alt === ' ') && $el.closest('a[href]')) {
            if ($el.closest('a[href]').getAttribute('tabindex') === '-1' && $el.closest('a[href]').getAttribute('aria-hidden') === 'true') ; else if ($el.closest('a[href]').getAttribute('aria-hidden') === 'true') {
              $el.classList.add('sa11y-error-border');
              $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('LINK_IMAGE_ARIA_HIDDEN')));
            } else if (this.fnIgnore($el.closest('a[href]'), 'noscript').textContent.trim().length === 0) {
              $el.classList.add('sa11y-error-border');
              $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('LINK_IMAGE_NO_ALT_TEXT')));
            } else {
              $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(GOOD, Lang._('LINK_IMAGE_HAS_TEXT')));
            }
          } else if (alt.length > 250 && $el.closest('a[href]')) {
            // Link and contains alt text.
            $el.classList.add('sa11y-warning-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('LINK_IMAGE_LONG_ALT', altLength, altText)));
          } else if (alt !== '' && $el.closest('a[href]') && this.fnIgnore($el.closest('a[href]'), 'noscript').textContent.trim().length === 0) {
            // Link and contains an alt text.
            $el.classList.add('sa11y-warning-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('LINK_IMAGE_ALT_WARNING', altText)));
          } else if (alt !== '' && $el.closest('a[href]') && this.fnIgnore($el.closest('a[href]'), 'noscript').textContent.trim().length >= 1) {
            // Contains alt text & surrounding link text.
            $el.classList.add('sa11y-warning-border');
            $el.closest('a[href]').insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('LINK_IMAGE_ALT_AND_TEXT_WARNING', altText)));
          } else if (alt === '' || alt === ' ') {
            // Decorative alt and not a link.
            if ($el.closest('figure')) {
              const figcaption = $el.closest('figure').querySelector('figcaption');
              if (figcaption !== null && figcaption.textContent.trim().length >= 1) {
                $el.classList.add('sa11y-warning-border');
                $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('IMAGE_FIGURE_DECORATIVE')));
              } else {
                $el.classList.add('sa11y-warning-border');
                $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('IMAGE_DECORATIVE')));
              }
            } else {
              $el.classList.add('sa11y-warning-border');
              $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('IMAGE_DECORATIVE')));
            }
          } else if (alt.length > 250) {
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('IMAGE_ALT_TOO_LONG', altLength, altText)));
          } else if (alt !== '') {
            // Figure element has same alt and caption text.
            if ($el.closest('figure')) {
              const figcaption = $el.closest('figure').querySelector('figcaption');
              if (!!figcaption
                && (figcaption.textContent.trim().toLowerCase() === altText.trim().toLowerCase())) {
                $el.classList.add('sa11y-warning-border');
                $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('IMAGE_FIGURE_DUPLICATE_ALT', altText)));
              } else {
                $el.insertAdjacentHTML('beforebegin', this.annotate(GOOD, Lang.sprintf('IMAGE_PASS', altText)));
              }
            } else {
              // If image has alt text - pass!
              $el.insertAdjacentHTML('beforebegin', this.annotate(GOOD, Lang.sprintf('IMAGE_PASS', altText)));
            }
          }
        }
      });
    };

    // ============================================================
    // Rulesets: Labels
    // ============================================================
    this.checkLabels = () => {
      this.inputs.forEach(($el) => {
        // Ignore hidden inputs.
        if (this.isElementHidden($el) !== true) {
          let ariaLabel = this.computeAriaLabel($el);
          const type = $el.getAttribute('type');
          const tabindex = $el.getAttribute('tabindex');

          // If button type is submit or button: pass
          if (type === 'submit' || type === 'button' || type === 'hidden' || tabindex === '-1') ; else if (type === 'image') {
            // Inputs where type="image".
            const imgalt = $el.getAttribute('alt');
            if (!imgalt || imgalt === ' ') {
              if ($el.getAttribute('aria-label')) ; else {
                $el.classList.add('sa11y-error-border');
                $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang._('LABELS_MISSING_IMAGE_INPUT_MESSAGE'), true));
              }
            }
          } else if (type === 'reset') {
            // Recommendation to remove reset buttons.
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang._('LABELS_INPUT_RESET_MESSAGE'), true));
          } else if ($el.getAttribute('aria-label') || $el.getAttribute('aria-labelledby') || $el.getAttribute('title')) {
            // Uses ARIA. Warn them to ensure there's a visible label.
            if ($el.getAttribute('title')) {
              ariaLabel = $el.getAttribute('title');
              $el.classList.add('sa11y-warning-border');
              $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang.sprintf('LABELS_ARIA_LABEL_INPUT_MESSAGE', ariaLabel), true));
            } else {
              $el.classList.add('sa11y-warning-border');
              $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang.sprintf('LABELS_ARIA_LABEL_INPUT_MESSAGE', ariaLabel), true));
            }
          } else if ($el.closest('label') && $el.closest('label').textContent.trim()) ; else if ($el.getAttribute('id')) {
            // Has an ID but doesn't have a matching FOR attribute.
            const $labels = this.root.querySelectorAll('label');
            let hasFor = false;

            $labels.forEach(($l) => {
              if (hasFor) return;
              if ($l.getAttribute('for') === $el.getAttribute('id')) {
                hasFor = true;
              }
            });

            if (!hasFor) {
              $el.classList.add('sa11y-error-border');
              const id = $el.getAttribute('id');
              $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang.sprintf('LABELS_NO_FOR_ATTRIBUTE_MESSAGE', id), true));
            }
          } else {
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang._('LABELS_MISSING_LABEL_MESSAGE'), true));
          }
        }
      });
    };

    // ============================================================
    // Rulesets: Embedded content.
    // ============================================================
    this.checkEmbeddedContent = () => {
      // Warning: Audio content.
      if (option.embeddedContentAudio === true) {
        this.audio.forEach(($el) => {
          $el.classList.add('sa11y-warning-border');
          $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('EMBED_AUDIO')));
        });
      }

      // Warning: Video content.
      if (option.embeddedContentVideo === true) {
        this.videos.forEach(($el) => {
          const track = $el.getElementsByTagName('TRACK');
          if ($el.tagName === 'VIDEO' && track.length) ; else {
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('EMBED_VIDEO')));
          }
        });
      }

      // Warning: Data visualizations.
      if (option.embeddedContentDataViz === true) {
        this.datavisualizations.forEach(($el) => {
          $el.classList.add('sa11y-warning-border');
          $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('EMBED_DATA_VIZ')));
        });
      }

      // Error: iFrame is missing accessible name.
      if (option.embeddedContentTitles === true) {
        this.iframes.forEach(($el) => {
          if ($el.tagName === 'VIDEO'
          || $el.tagName === 'AUDIO'
          || $el.getAttribute('aria-hidden') === 'true'
          || $el.getAttribute('hidden') !== null
          || $el.style.display === 'none'
          || $el.getAttribute('role') === 'presentation') ; else if ($el.getAttribute('title') === null || $el.getAttribute('title') === '') {
            if ($el.getAttribute('aria-label') === null || $el.getAttribute('aria-label') === '') {
              if ($el.getAttribute('aria-labelledby') === null) {
                // Make sure red error border takes precedence
                if ($el.classList.contains('sa11y-warning-border')) {
                  $el.classList.remove('sa11y-warning-border');
                }
                $el.classList.add('sa11y-error-border');
                $el.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('EMBED_MISSING_TITLE')));
              }
            }
          } else ;
        });
      }

      // Warning: general warning for iFrames
      if (option.embeddedContentGeneral === true) {
        this.embeddedContent.forEach(($el) => {
          if ($el.tagName === 'VIDEO'
          || $el.tagName === 'AUDIO'
          || $el.getAttribute('aria-hidden') === 'true'
          || $el.getAttribute('hidden') !== null
          || $el.style.display === 'none'
          || $el.getAttribute('role') === 'presentation'
          || $el.getAttribute('tabindex') === '-1') ; else {
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('EMBED_GENERAL_WARNING')));
          }
        });
      }
    };

    // ============================================================
    // Rulesets: QA
    // ============================================================
    this.checkQA = () => {
      // Error: Find all links pointing to development environment.
      if (option.badLinksQA === true) {
        this.customErrorLinks.forEach(($el) => {
          $el.classList.add('sa11y-error-text');
          $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang.sprintf('QA_BAD_LINK', $el), true));
        });
      }

      // Warning: Excessive bolding or italics.
      if (option.strongItalicsQA === true) {
        this.strongitalics.forEach(($el) => {
          const strongItalicsText = $el.textContent.trim().length;
          if (strongItalicsText > 400) {
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('QA_BAD_ITALICS')));
            $el.parentNode.classList.add('sa11y-warning-border');
          }
        });
      }

      // Warning: Find all PDFs.
      if (option.pdfQA === true) {
        this.pdf.forEach(($el, i) => {
          const pdfCount = this.pdf.length;

          // Highlight all PDFs.
          if (pdfCount > 0) {
            $el.classList.add('sa11y-warning-text');
          }
          // Only append warning button to first PDF.
          if ($el && i === 0) {
            $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang.sprintf('QA_PDF', pdfCount), true));
            if ($el.querySelector('img')) {
              $el.classList.remove('sa11y-warning-text');
            }
          }
        });
      }

      // Error: Missing language tag. Lang should be at least 2 characters.
      if (option.langQA === true) {
        if (!this.language || this.language.length < 2) {
          this.panel.insertAdjacentHTML('afterend', this.annotateBanner(ERROR, Lang._('QA_PAGE_LANGUAGE')));
        }
      }

      // Warning: Find blockquotes used as headers.
      if (option.blockquotesQA === true) {
        this.blockquotes.forEach(($el) => {
          const bqHeadingText = $el.textContent;
          if (bqHeadingText.trim().length < 25) {
            $el.classList.add('sa11y-warning-border');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('QA_BLOCKQUOTE_MESSAGE', bqHeadingText)));
          }
        });
      }

      // Tables check.
      if (option.tablesQA === true) {
        this.tables.forEach(($el) => {
          const findTHeaders = $el.querySelectorAll('th');
          const findHeadingTags = $el.querySelectorAll('h1, h2, h3, h4, h5, h6');
          if (findTHeaders.length === 0) {
            $el.classList.add('sa11y-error-border');
            $el.insertAdjacentHTML('beforebegin',
              this.annotate(ERROR, Lang._('TABLES_MISSING_HEADINGS')));
          }
          if (findHeadingTags.length > 0) {
            findHeadingTags.forEach(($a) => {
              $a.classList.add('sa11y-error-border');
              $a.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang._('TABLES_SEMANTIC_HEADING')));
            });
          }
          findTHeaders.forEach(($b) => {
            if ($b.textContent.trim().length === 0) {
              $b.classList.add('sa11y-error-border');
              $b.insertAdjacentHTML('afterbegin', this.annotate(ERROR, Lang._('TABLES_EMPTY_HEADING')));
            }
          });
        });
      }

      // Warning: Detect fake headings.
      if (option.fakeHeadingsQA === true) {
        this.paragraphs.forEach(($el) => {
          const brAfter = $el.innerHTML.indexOf('</strong><br>');
          const brBefore = $el.innerHTML.indexOf('<br></strong>');
          let boldtext;

          // Check paragraphs greater than x characters.
          if ($el && $el.textContent.trim().length >= 300) {
            const { firstChild } = $el;

            // If paragraph starts with <strong> tag and ends with <br>.
            if (firstChild.tagName === 'STRONG' && (brBefore !== -1 || brAfter !== -1)) {
              boldtext = firstChild.textContent;

              if (!/[*]$/.test(boldtext) && !$el.closest('table') && boldtext.length <= 120) {
                firstChild.classList.add('sa11y-fake-heading', 'sa11y-warning-border');
                $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('QA_FAKE_HEADING', boldtext)));
              }
            }
          }

          // If paragraph only contains <p><strong>...</strong></p>.
          if (/^<(strong)>.+<\/\1>$/.test($el.innerHTML.trim())) {
            // Although only flag if it:
            // 1) Has less than 120 characters (typical heading length).
            // 2) The previous element is not a heading.
            const prevElement = $el.previousElementSibling;
            let tagName = '';
            boldtext = $el.textContent;

            if (prevElement !== null) {
              tagName = prevElement.tagName;
            }

            if (!/[*]$/.test(boldtext) && !$el.closest('table') && boldtext.length <= 120 && tagName.charAt(0) !== 'H') {
              $el.classList.add('sa11y-fake-heading', 'sa11y-warning-border');
              $el.insertAdjacentHTML('beforebegin',
                this.annotate(WARNING, Lang.sprintf('QA_FAKE_HEADING', boldtext)));
            }
          }
        });
      }

      // Warning: Detect paragraphs that should be lists.
      // Thanks to John Jameson from PrincetonU for this ruleset!
      if (option.fakeListQA === true) {
        this.paragraphs.forEach(($el) => {
          let activeMatch = '';
          const prefixDecrement = {
            b: 'a',
            B: 'A',
            2: '1',
            б: 'а',
            Б: 'А',
          };
          const prefixMatch = /a\.|a\)|A\.|A\)|а\.|а\)|А\.|А\)|1\.|1\)|\*\s|-\s|--|•\s|→\s|✓\s|✔\s|✗\s|✖\s|✘\s|❯\s|›\s|»\s/;
          const decrement = (el) => el.replace(/^b|^B|^б|^Б|^2/, (match) => prefixDecrement[match]);
          let hit = false;
          const firstPrefix = $el.textContent.substring(0, 2);
          if (
            firstPrefix.trim().length > 0
            && firstPrefix !== activeMatch
            && firstPrefix.match(prefixMatch)
          ) {
            const hasBreak = $el.innerHTML.indexOf('<br>');
            if (hasBreak !== -1) {
              const subParagraph = $el
                .innerHTML
                .substring(hasBreak + 4)
                .trim();
              const subPrefix = subParagraph.substring(0, 2);
              if (firstPrefix === decrement(subPrefix)) {
                hit = true;
              }
            }

            // Decrement the second p prefix and compare .
            if (!hit) {
              const $second = this.getNextSibling($el, 'p');
              if ($second) {
                const secondPrefix = decrement($el.nextElementSibling.textContent.substring(0, 2));
                if (firstPrefix === secondPrefix) {
                  hit = true;
                }
              }
            }
            if (hit) {
              $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('QA_SHOULD_BE_LIST', firstPrefix)));
              $el.classList.add('sa11y-warning-border');
              activeMatch = firstPrefix;
            } else {
              activeMatch = '';
            }
          } else {
            activeMatch = '';
          }
        });
      }

      // Warning: Detect uppercase. Updated logic thanks to Editoria11y!
      if (option.allCapsQA === true) {
        const checkCaps = ($el) => {
          let thisText = '';
          if ($el.tagName === 'LI') {
            // Prevent recursion through nested lists.
            $el.childNodes.forEach((node) => {
              if (node.nodeType === 3) {
                thisText += node.textContent;
              }
            });
          } else {
            thisText = this.getText($el);
          }
          const uppercasePattern = /([A-Z]{2,}[ ])([A-Z]{2,}[ ])([A-Z]{2,}[ ])([A-Z]{2,})/g;
          const detectUpperCase = thisText.match(uppercasePattern);

          if (detectUpperCase && detectUpperCase[0].length > 10) {
            const parentClickable = $el.closest('a, button');
            if (parentClickable) {
              parentClickable.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('QA_UPPERCASE_WARNING')));
              parentClickable.classList.add('sa11y-warning-border');
            } else {
              $el.classList.add('sa11y-warning-border');
              $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('QA_UPPERCASE_WARNING')));
            }
          }
        };
        this.paragraphs.forEach(($el) => checkCaps($el));
        this.headings.forEach(($el) => checkCaps($el));
        this.lists.forEach(($el) => checkCaps($el));
        this.blockquotes.forEach(($el) => checkCaps($el));
      }

      // Error: Duplicate IDs
      if (option.duplicateIdQA === true) {
        const ids = Array.from(this.root.querySelectorAll('[id]'));
        const allIds = {};
        ids.forEach(($el) => {
          const { id } = $el;
          if (id) {
            if (allIds[id] === undefined) {
              allIds[id] = 1;
            } else {
              $el.classList.add('sa11y-error-border');
              $el.insertAdjacentHTML('afterend', this.annotate(ERROR, Lang.sprintf('QA_DUPLICATE_ID', id), true));
            }
          }
        });
      }

      // Warning: Flag underline text.
      if (option.underlinedTextQA === true) {
        // Find all <u> tags.
        const underline = Array.from(this.root.querySelectorAll('u'));
        underline.forEach(($el) => {
          $el.classList.add('sa11y-warning-text');
          $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('QA_TEXT_UNDERLINE_WARNING'), true));
        });
        // Find underline based on computed style.
        const computeUnderline = ($el) => {
          const style = getComputedStyle($el);
          const decoration = style.textDecorationLine;
          if (decoration === 'underline') {
            $el.classList.add('sa11y-warning-text');
            $el.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang._('QA_TEXT_UNDERLINE_WARNING')));
          }
        };
        this.paragraphs.forEach(($el) => computeUnderline($el));
        this.headings.forEach(($el) => computeUnderline($el));
        this.lists.forEach(($el) => computeUnderline($el));
        this.blockquotes.forEach(($el) => computeUnderline($el));
        this.spans.forEach(($el) => computeUnderline($el));
      }

      // Error: Page is missing meta title.
      if (option.pageTitleQA === true) {
        const $title = document.querySelector('title');
        if (!$title || $title.textContent.trim().length === 0) {
          this.panel.insertAdjacentHTML('afterend', this.annotateBanner(ERROR, Lang._('QA_PAGE_TITLE')));
        }
      }

      // Warning: Find inappropriate use of <sup> and <sub> tags.
      if (option.subscriptQA === true) {
        const $subscript = Array.from(this.root.querySelectorAll('sup, sub'));
        $subscript.forEach(($el) => {
          if ($el.textContent.trim().length >= 80) {
            $el.classList.add('sa11y-warning-text');
            $el.insertAdjacentHTML('afterend', this.annotate(WARNING, Lang._('QA_SUBSCRIPT_WARNING'), true));
          }
        });
      }
    };

    // ============================================================
    // Rulesets: Contrast
    // Color contrast plugin by jasonday: https://github.com/jasonday/color-contrast
    // ============================================================
    /* eslint-disable */
    this.checkContrast = () => {
      let contrastErrors = {
        errors: [],
        warnings: [],
      };

      const elements = this.contrast;
      const contrast = {
        // Parse rgb(r, g, b) and rgba(r, g, b, a) strings into an array.
        // Adapted from https://github.com/gka/chroma.js
        parseRgb(css) {
          let i;
          let m;
          let rgb;
          let f;
          let k;
          if (m = css.match(/rgb\(\s*(\-?\d+),\s*(\-?\d+)\s*,\s*(\-?\d+)\s*\)/)) {
            rgb = m.slice(1, 4);
            for (i = f = 0; f <= 2; i = ++f) {
              rgb[i] = +rgb[i];
            }
            rgb[3] = 1;
          } else if (m = css.match(/rgba\(\s*(\-?\d+),\s*(\-?\d+)\s*,\s*(\-?\d+)\s*,\s*([01]|[01]?\.\d+)\)/)) {
            rgb = m.slice(1, 5);
            for (i = k = 0; k <= 3; i = ++k) {
              rgb[i] = +rgb[i];
            }
          }
          return rgb;
        },
        // Based on http://www.w3.org/TR/WCAG20/#relativeluminancedef
        relativeLuminance(c) {
          const lum = [];
          for (let i = 0; i < 3; i++) {
            const v = c[i] / 255;
            // eslint-disable-next-line no-restricted-properties
            lum.push(v < 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4));
          }
          return (0.2126 * lum[0]) + (0.7152 * lum[1]) + (0.0722 * lum[2]);
        },
        // Based on http://www.w3.org/TR/WCAG20/#contrast-ratiodef
        contrastRatio(x, y) {
          const l1 = contrast.relativeLuminance(contrast.parseRgb(x));
          const l2 = contrast.relativeLuminance(contrast.parseRgb(y));
          return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
        },

        getBackground(el) {
          const styles = getComputedStyle(el);
          const bgColor = styles.backgroundColor;
          const bgImage = styles.backgroundImage;
          const rgb = `${contrast.parseRgb(bgColor)}`;
          const alpha = rgb.split(',');

          // if background has alpha transparency, flag manual check
          if (alpha[3] < 1 && alpha[3] > 0) {
            return 'alpha';
          }

          // if element has no background image, or transparent return bgColor
          if (bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent' && bgImage === 'none' && alpha[3] !== '0') {
            return bgColor;
          } if (bgImage !== 'none') {
            return 'image';
          }

          // retest if not returned above
          if (el.tagName === 'HTML') {
            return 'rgb(255, 255, 255)';
          }
          return contrast.getBackground(el.parentNode);
        },
        check() {
          // resets results
          contrastErrors = {
            errors: [],
            warnings: [],
          };

          for (let i = 0; i < elements.length; i++) {
            const elem = elements[i];
            if (contrast) {
              const style = getComputedStyle(elem);
              const { color } = style;
              const { fill } = style;
              const fontSize = parseInt(style.fontSize, 10);
              const pointSize = fontSize * (3 / 4);
              const { fontWeight } = style;
              const htmlTag = elem.tagName;
              const background = contrast.getBackground(elem);
              const textString = [].reduce.call(elem.childNodes, (a, b) => a + (b.nodeType === 3 ? b.textContent : ''), '');
              const text = textString.trim();
              let ratio;
              let error;
              let warning;

              if (htmlTag === 'SVG') {
                ratio = Math.round(contrast.contrastRatio(fill, background) * 100) / 100;
                if (ratio < 3) {
                  error = {
                    elem,
                    ratio: `${ratio}:1`,
                  };
                  contrastErrors.errors.push(error);
                }
              } else if (text.length || htmlTag === 'INPUT' || htmlTag === 'SELECT' || htmlTag === 'TEXTAREA') {
                // does element have a background image - needs to be manually reviewed
                if (background === 'image') {
                  warning = {
                    elem,
                  };
                  contrastErrors.warnings.push(warning);
                } else if (background === 'alpha') {
                  warning = {
                    elem,
                  };
                  contrastErrors.warnings.push(warning);
                } else {
                  ratio = Math.round(contrast.contrastRatio(color, background) * 100) / 100;
                  if (pointSize >= 18 || (pointSize >= 14 && fontWeight >= 700)) {
                    if (ratio < 3) {
                      error = {
                        elem,
                        ratio: `${ratio}:1`,
                      };
                      contrastErrors.errors.push(error);
                    }
                  } else if (ratio < 4.5) {
                    error = {
                      elem,
                      ratio: `${ratio}:1`,
                    };
                    contrastErrors.errors.push(error);
                  }
                }
              }
            }
          }
          return contrastErrors;
        },
      };

      contrast.check();

      contrastErrors.errors.forEach((item) => {
        const name = item.elem;
        const cratio = item.ratio;
        const clone = name.cloneNode(true);
        const removeSa11yHeadingLabel = clone.querySelectorAll('.sa11y-heading-label');
        for (let i = 0; i < removeSa11yHeadingLabel.length; i++) {
          clone.removeChild(removeSa11yHeadingLabel[i]);
        }

        const nodetext = this.fnIgnore(clone, 'script').textContent;
        if (name.tagName === 'INPUT') {
          name.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('CONTRAST_INPUT_ERROR', cratio)));
        } else {
          name.insertAdjacentHTML('beforebegin', this.annotate(ERROR, Lang.sprintf('CONTRAST_ERROR', cratio, nodetext)));
        }
      });

      contrastErrors.warnings.forEach((item) => {
        const name = item.elem;
        const clone = name.cloneNode(true);
        const removeSa11yHeadingLabel = clone.querySelectorAll('.sa11y-heading-label');
        for (let i = 0; i < removeSa11yHeadingLabel.length; i++) {
          clone.removeChild(removeSa11yHeadingLabel[i]);
        }
        const nodetext = this.fnIgnore(clone, 'script').textContent;
        name.insertAdjacentHTML('beforebegin', this.annotate(WARNING, Lang.sprintf('CONTRAST_WARNING', nodetext)));
      });
    };
    /* eslint-disable */
    // ============================================================
    // Rulesets: Readability
    // Adapted from Greg Kraus' readability script: https://accessibility.oit.ncsu.edu/it-accessibility-at-nc-state/developers/tools/readability-bookmarklet/
    // ============================================================
    this.checkReadability = () => {
      // Crude hack to add a period to the end of list items to make a complete sentence.
      this.readability.forEach(($el) => {
        const listText = $el.textContent;
        if (listText.length >= 120) {
          if (listText.charAt(listText.length - 1) !== '.') {
            $el.insertAdjacentHTML('beforeend', "<span class='sa11y-readability-period sa11y-visually-hidden'>.</span>");
          }
        }
      });

      // Combine all page text.
      const readabilityarray = [];
      for (let i = 0; i < this.readability.length; i++) {
        const current = this.readability[i];
        if (this.getText(current) !== '') {
          readabilityarray.push(current.textContent);
        }
      }
      const pageText = readabilityarray.join(' ').trim().toString();

      /* Flesch Reading Ease for English, French, German, Dutch, and Italian.
        Reference: https://core.ac.uk/download/pdf/6552422.pdf
        Reference: https://github.com/Yoast/YoastSEO.js/issues/267 */
      if (['en', 'fr', 'de', 'nl', 'it'].includes(option.readabilityLang)) {
        // Compute syllables: http://stackoverflow.com/questions/5686483/how-to-compute-number-of-syllables-in-a-word-in-javascript
        const numberOfSyllables = (el) => {
          let wordCheck = el;
          wordCheck = wordCheck.toLowerCase().replace('.', '').replace('\n', '');
          if (wordCheck.length <= 3) {
            return 1;
          }
          wordCheck = wordCheck.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/, '');
          wordCheck = wordCheck.replace(/^y/, '');
          const syllableString = wordCheck.match(/[aeiouy]{1,2}/g);
          let syllables = 0;

          const syllString = !!syllableString;
          if (syllString) {
            syllables = syllableString.length;
          }
          return syllables;
        };

        // Words
        const wordsRaw = pageText.replace(/[.!?-]+/g, ' ').split(' ');
        let words = 0;
        for (let i = 0; i < wordsRaw.length; i++) {
        // eslint-disable-next-line eqeqeq
          if (wordsRaw[i] != 0) {
            words += 1;
          }
        }

        // Sentences
        const sentenceRaw = pageText.split(/[.!?]+/);
        let sentences = 0;
        for (let i = 0; i < sentenceRaw.length; i++) {
          if (sentenceRaw[i] !== '') {
            sentences += 1;
          }
        }

        // Syllables
        let totalSyllables = 0;
        let syllables1 = 0;
        let syllables2 = 0;
        for (let i = 0; i < wordsRaw.length; i++) {
        // eslint-disable-next-line eqeqeq
          if (wordsRaw[i] != 0) {
            const syllableCount = numberOfSyllables(wordsRaw[i]);
            if (syllableCount === 1) {
              syllables1 += 1;
            }
            if (syllableCount === 2) {
              syllables2 += 1;
            }
            totalSyllables += syllableCount;
          }
        }

        let flesch = false;
        if (option.readabilityLang === 'en') {
          flesch = 206.835 - (1.015 * (words / sentences)) - (84.6 * (totalSyllables / words));
        } else if (option.readabilityLang === 'fr') {
          flesch = 207 - (1.015 * (words / sentences)) - (73.6 * (totalSyllables / words));
        } else if (option.readabilityLang === 'es') {
          flesch = 206.84 - (1.02 * (words / sentences)) - (0.60 * (100 * (totalSyllables / words)));
        } else if (option.readabilityLang === 'de') {
          flesch = 180 - (words / sentences) - (58.5 * (totalSyllables / words));
        } else if (option.readabilityLang === 'nl') {
          flesch = 206.84 - (0.77 * (100 * (totalSyllables / words))) - (0.93 * (words / sentences));
        } else if (option.readabilityLang === 'it') {
          flesch = 217 - (1.3 * (words / sentences)) - (0.6 * (100 * (totalSyllables / words)));
        }

        // Update panel.
        const $readabilityinfo = document.getElementById('sa11y-readability-info');

        if (pageText.length === 0) {
          $readabilityinfo.innerHTML = Lang._('READABILITY_NO_P_OR_LI_MESSAGE');
        } else if (words > 30) {
          // Score must be between 0 and 100%.
          if (flesch > 100) {
            flesch = 100;
          } else if (flesch < 0) {
            flesch = 0;
          }

          const fleschScore = flesch.toFixed(1);
          const avgWordsPerSentence = (words / sentences).toFixed(1);
          const complexWords = Math.round(100 * ((words - (syllables1 + syllables2)) / words));

          // Flesch score: WCAG AAA pass if greater than 60
          if (fleschScore >= 0 && fleschScore < 30) {
            $readabilityinfo.innerHTML = `${fleschScore} <span class="sa11y-readability-score">${Lang._('LANG_VERY_DIFFICULT')}</span>`;
          } else if (fleschScore > 31 && fleschScore < 49) {
            $readabilityinfo.innerHTML = `${fleschScore} <span class="sa11y-readability-score">${Lang._('LANG_DIFFICULT')}</span>`;
          } else if (fleschScore > 50 && fleschScore < 60) {
            $readabilityinfo.innerHTML = `${fleschScore} <span class="sa11y-readability-score">${Lang._('LANG_FAIRLY_DIFFICULT')}</span>`;
          } else {
            $readabilityinfo.innerHTML = `${fleschScore} <span class="sa11y-readability-score">${Lang._('LANG_GOOD')}</span>`;
          }
          // Flesch details
          document.getElementById('sa11y-readability-details').innerHTML = `
          <li><strong>${Lang._('LANG_AVG_SENTENCE')}</strong> ${avgWordsPerSentence}</li>
          <li><strong>${Lang._('LANG_COMPLEX_WORDS')}</strong> ${complexWords}%</li>
          <li><strong>${Lang._('LANG_TOTAL_WORDS')}</strong> ${words}</li>`;
        } else {
          $readabilityinfo.textContent = Lang._('READABILITY_NOT_ENOUGH_CONTENT_MESSAGE');
        }
      }

      /* Lix: Danish, Finnish, Norwegian (Bokmål & Nynorsk), Swedish. To-do: More research needed.
      Reference: https://www.simoahava.com/analytics/calculate-readability-scores-for-content/#commento-58ac602191e5c6dc391015c5a6933cf3e4fc99d1dc92644024c331f1ee9b6093 */
      if (['sv', 'fi', 'da', 'no', 'nb', 'nn'].includes(option.readabilityLang)) {
        const calculateLix = (text) => {
          const lixWords = () => text.replace(/[-'.]/ig, '').split(/[^a-zA-ZöäåÖÄÅÆæØø0-9]/g).filter(Boolean);
          const splitSentences = () => {
            const splitter = /\?|!|\.|\n/g;
            const arrayOfSentences = text.split(splitter).filter(Boolean);
            return arrayOfSentences;
          };
          const wordCount = lixWords().length;
          const longWordsCount = lixWords().filter((wordsArray) => wordsArray.length > 6).length;
          const sentenceCount = splitSentences().length;
          const score = Math.round((wordCount / sentenceCount) + ((longWordsCount * 100) / wordCount));
          const avgWordsPerSentence = (wordCount / sentenceCount).toFixed(1);
          const complexWords = Math.round(100 * (longWordsCount / wordCount));
          return {
            score, avgWordsPerSentence, complexWords, wordCount,
          };
        };

        // Update panel.
        const $readabilityinfo = document.getElementById('sa11y-readability-info');
        const lix = calculateLix(pageText);

        if (pageText.length === 0) {
          $readabilityinfo.innerHTML = Lang._('READABILITY_NO_P_OR_LI_MESSAGE');
        } else if (lix.wordCount > 30) {
          if (lix.score >= 0 && lix.score < 39) {
            $readabilityinfo.innerHTML = `${lix.score} <span class="sa11y-readability-score">${Lang._('LANG_GOOD')}</span>`;
          } else if (lix.score > 40 && lix.score < 50) {
            $readabilityinfo.innerHTML = `${lix.score} <span class="sa11y-readability-score">${Lang._('LANG_FAIRLY_DIFFICULT')}</span>`;
          } else if (lix.score > 51 && lix.score < 61) {
            $readabilityinfo.innerHTML = `${lix.score} <span class="sa11y-readability-score">${Lang._('LANG_DIFFICULT')}</span>`;
          } else {
            $readabilityinfo.innerHTML = `${lix.score} <span class="sa11y-readability-score">${Lang._('LANG_VERY_DIFFICULT')}</span>`;
          }
          // LIX details
          document.getElementById('sa11y-readability-details').innerHTML = `
            <li><strong>${Lang._('LANG_AVG_SENTENCE')}</strong> ${lix.avgWordsPerSentence}</li>
            <li><strong>${Lang._('LANG_COMPLEX_WORDS')}</strong> ${lix.complexWords}%</li>
            <li><strong>${Lang._('LANG_TOTAL_WORDS')}</strong> ${lix.wordCount}</li>`;
        } else {
          $readabilityinfo.textContent = Lang._('READABILITY_NOT_ENOUGH_CONTENT_MESSAGE');
        }
      }
    };
    this.initialize();
  }
}

export { Lang, Sa11y, Sa11yCustomChecks };
