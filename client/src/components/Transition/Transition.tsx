import PropTypes from 'prop-types';
import React from 'react';

import CSSTransitionGroup from 'react-transition-group/CSSTransitionGroup';

const TRANSITION_DURATION = 210;

// The available transitions. Must match the class names in CSS.
export const PUSH = 'push';
export const POP = 'pop';

/**
 * Wrapper around react-transition-group with default values.
 */
const Transition = ({ name, component, className, duration, children }) => (
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
  name: PropTypes.oneOf([PUSH, POP]).isRequired,
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
