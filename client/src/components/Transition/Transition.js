import PropTypes from 'prop-types';
import React from 'react';

import CSSTransitionGroup from 'react-addons-css-transition-group';

const TRANSITION_DURATION = 210;

// The available transitions. Must match the class names in CSS.
export const PUSH = 'push';
export const POP = 'pop';
export const FADE = 'fade';

/**
 * Wrapper arround react-addons-css-transition-group with default values.
 */
const Transition = ({
  name,
  component,
  className,
  duration,
  children,
}) => (
  <CSSTransitionGroup
    component={component}
    transitionEnterTimeout={duration}
    transitionLeaveTimeout={duration}
    transitionName={`c-transition-${name}`}
    className={className}
  >
    {children}
  </CSSTransitionGroup>
);

Transition.propTypes = {
  name: PropTypes.oneOf([PUSH, POP, FADE]).isRequired,
  component: PropTypes.string,
  className: PropTypes.string,
  duration: PropTypes.number,
  children: PropTypes.node,
};

Transition.defaultProps = {
  component: 'div',
  children: null,
  className: null,
  duration: TRANSITION_DURATION,
};

export default Transition;
