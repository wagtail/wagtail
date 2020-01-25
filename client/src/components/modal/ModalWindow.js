import React, { useEffect, useRef, useState } from 'react';
import FocusTrap from 'react-focus-trap';
import PropTypes from 'prop-types';
import _ from 'lodash';

import ModalHeader from './ModalHeader';
import ModalSpinner from './ModalSpinner';

const propTypes = {
  heading: PropTypes.string.isRequired,
  onSearch: PropTypes.func,
  searchEnabled: PropTypes.bool.isRequired,
  isLoading: PropTypes.bool,
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

  // Control modal visibility
  // The modal shouldn't become visible until it's either loaded or has been loading
  // for some time
  const [modalVisible, setModalVisible] = useState(false);
  useEffect(() => {
    if (!modalVisible && !props.isLoading) {
      // Content finished loading
      setModalVisible(true);
    }
  }, [props.isLoading]);
  useEffect(() => {
    // If the content is taking a long time to load, show the modal
    // anyway.
    const timeout = setTimeout(() => {
      setModalVisible(true);
    }, 1000);

    return () => {
      clearTimeout(timeout);
    };
  });

  // Control loading spinner
  // Only show it if loading is taking a while, so it doesn't flash as you type
  const [loadingSpinnerVisible, setLoadingSpinnerVisible] = useState(false);
  useEffect(() => {
    setLoadingSpinnerVisible(false);

    // Creating timeout every time (even if it isn't loading) seems to be much more reliable
    const timeout = setTimeout(() => {
      if (props.isLoading) {
        setLoadingSpinnerVisible(true);
      }
    }, 100);

    return () => {
      clearTimeout(timeout);
    };
  }, [props.isLoading]);

  const modalStyle = {
    display: modalVisible ? 'block' : 'none',
  };
  const modalClasses = ['modal', 'fade'];

  const overlayStyle = {};
  const overlayClasses = ['modal-backdrop', 'fade'];

  if (modalVisible) {
    modalClasses.push('in');
    overlayClasses.push('in');
  } else {
    overlayStyle.cursor = 'wait';
  }

  return (
    <div>
      <div
        className={modalClasses.join(' ')}
        tabIndex={-1}
        role="dialog"
        aria-modal={true}
        aria-hidden={!modalVisible}
        style={modalStyle}
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
                <ModalSpinner isActive={props.isLoading && loadingSpinnerVisible}>
                  {props.children}
                </ModalSpinner>
              </div>
            </div>
          </div>
        </FocusTrap>
      </div>
      <div className={overlayClasses.join(' ')} style={overlayStyle} />
    </div>
  );
}

ModalWindow.propTypes = propTypes;

export default ModalWindow;
