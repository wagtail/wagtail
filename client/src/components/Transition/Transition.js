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
  name: React.PropTypes.oneOf([PUSH, POP, FADE]).isRequired,
  component: React.PropTypes.string,
  className: React.PropTypes.string,
  duration: React.PropTypes.number,
  children: React.PropTypes.node,
};

Transition.defaultProps = {
  component: 'div',
  children: null,
  className: null,
  duration: TRANSITION_DURATION,
};

export default Transition;
