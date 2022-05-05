import PropTypes from 'prop-types';
import React from 'react';

const TOP = 'top';
const LEFT = 'left';
const TOP_LEFT = 'top-left';

const getTooltipStyles = (target, direction) => {
  const top = window.pageYOffset + target.top;
  const left = window.pageXOffset + target.left;
  switch (direction) {
    case TOP:
      return {
        top: top + target.height,
        insetInlineStart: left + target.width / 2,
      };
    case LEFT:
      return {
        top: top + target.height / 2,
        insetInlineStart: left + target.width,
      };
    case TOP_LEFT:
    default:
      return {
        top: top + target.height,
        insetInlineStart: left,
      };
  }
};

/**
 * A tooltip, with arbitrary content.
 */
const Tooltip = ({ target, children, direction }) => (
  <div
    style={getTooltipStyles(target, direction)}
    className={`Tooltip Tooltip--${direction}`}
    role="tooltip"
  >
    {children}
  </div>
);

Tooltip.propTypes = {
  target: PropTypes.shape({
    top: PropTypes.number.isRequired,
    left: PropTypes.number.isRequired,
    width: PropTypes.number.isRequired,
    height: PropTypes.number.isRequired,
  }).isRequired,
  direction: PropTypes.oneOf([TOP, LEFT, TOP_LEFT]).isRequired,
  children: PropTypes.node.isRequired,
};

export default Tooltip;
