import React, { useEffect, useRef } from 'react';
import PropTypes from 'prop-types';

import { addFocusOutline } from '../../../utils/focus';

const propTypes = {
  isFocused: PropTypes.bool.isRequired,
  children: PropTypes.node.isRequired,
};

function FocusController(props) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current && props.isFocused) {
      ref.current.focus();

      addFocusOutline();
    }
  }, [props.isFocused]);

  return React.Children.map(props.children, element => React.cloneElement(element, { tabIndex: -1, ref }));
}

FocusController.propTypes = propTypes;

export default FocusController;
