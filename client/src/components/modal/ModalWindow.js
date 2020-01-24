import React, { useEffect, useRef } from 'react';
import FocusTrap from 'react-focus-trap';
import PropTypes from 'prop-types';
import _ from 'lodash';

import ModalHeader from './ModalHeader';
import ModalSpinner from './ModalSpinner';

const propTypes = {
  heading: PropTypes.string.isRequired,
  onSearch: PropTypes.func,
  searchEnabled: PropTypes.bool.isRequired,
  showLoadingSpinner: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  onKeyDown: PropTypes.func,
  children: PropTypes.node,
};

function ModalWindow(props) {
  const id = useRef();
  if (!id.current) {
    id.current = _.uniqueId('react-modal-');
  }

  const previousFocusedElement = useRef();

  useEffect(() => {
    // Save the currently focused element so we can reset it when the modal closes
    previousFocusedElement.current = document.activeElement;

    // Focus the search box
    document.getElementById(`${id.current}-search`).focus();

    // Watch for keydown events
    const keydownEventListener = e => {
      // Check for custom keydown event handler
      if (props.onKeyDown) {
        props.onKeyDown(e);

        if (e.defaultPrevented) {
          return;
        }
      }

      // Close modal on click escape
      if (e.key === 'Escape') {
        // Refocus the element that was focused when the modal was opened
        previousFocusedElement.current.focus();

        props.onClose(e);
      }
    };

    document.addEventListener('keydown', keydownEventListener);

    return () => {
      document.removeEventListener('keydown', keydownEventListener);
    };
  });

  const onClose = e => {
    // Refocus the element that was focused when the modal was opened
    previousFocusedElement.current.focus();

    props.onClose(e);
  };

  return (
    <div>
      <div
        className="modal fade in"
        tabIndex={-1}
        role="dialog"
        aria-modal={true}
        style={{ display: 'block' }}
        aria-labelledby={`${id.current}-title`}
      >
        <FocusTrap>
          <div className="modal-dialog">
            <div className="modal-content">
              <button
                onClick={onClose}
                type="button"
                className="button close icon text-replace icon-cross"
                data-dismiss="modal"
              >
                &times;
              </button>
              <div className="modal-body">
                <ModalHeader
                  heading={props.heading}
                  headingId={`${id.current}-title`}
                  searchId={`${id.current}-search`}
                  onSearch={props.onSearch}
                  searchEnabled={props.searchEnabled}
                />

                <ModalSpinner isActive={props.showLoadingSpinner}>
                  {props.children}
                </ModalSpinner>
              </div>
            </div>
          </div>
        </FocusTrap>
      </div>
      <div className="modal-backdrop fade in" />
    </div>
  );
}

ModalWindow.propTypes = propTypes;

export default ModalWindow;
