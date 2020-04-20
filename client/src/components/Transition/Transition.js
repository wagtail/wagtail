import PropTypes from 'prop-types';
import React from 'react';

import CSSTransitionGroup from 'react-transition-group/CSSTransitionGroup';

const TRANSITION_DURATION = 210;

// The available transitions. Must match the class names in CSS.
export const PUSH = 'push';
export const POP = 'pop';

/**
 * Wrapper arround react-transition-group with default values.
 */
const Transition = ({
  name,
  component,
  className,
  duration,
  children,
  label,
}) => (
  <CSSTransitionGroup
    component={component}
    transitionEnterTimeout={duration}
    transitionLeaveTimeout={duration}
    transitionName={`c-transition-${name}`}
    className={className}
    aria-label={label}
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
  label: PropTypes.string,
};

Transition.defaultProps = {
  component: 'div',
  children: null,
  className: null,
  duration: TRANSITION_DURATION,
  label: null,
};

export default Transition;
