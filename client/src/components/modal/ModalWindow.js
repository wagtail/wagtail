import React from 'react';
import FocusTrap from 'react-focus-trap';
import PropTypes from 'prop-types';

const propTypes = {
  onModalClose: PropTypes.func.isRequired,
};

class ModalWindow extends React.Component {
  componentWillMount() {
    // Save the currently focused element so we can reset it when the modal closes
    this.previousFocusedElement = document.activeElement;
  }

  render() {
    const onModalClose = e => {
      // Refocus the element that was focused when the modal was opened
      this.previousFocusedElement.focus();

      this.props.onModalClose(e);
    };

    return (
      <div>
        <div
          className="modal fade in"
          tabIndex={-1}
          role="dialog"
          aria-modal={true}
          style={{ display: 'block' }}
          {...this.props.extraProps}
        >
          <FocusTrap>
            <div className="modal-dialog">
              <div className="modal-content">
                <button
                  onClick={onModalClose}
                  type="button"
                  className="button close icon text-replace icon-cross"
                  data-dismiss="modal"
                >
                  &times;
                </button>
                <div className="modal-body">
                  {this.props.children}
                </div>
              </div>
            </div>
          </FocusTrap>
        </div>
        <div className="modal-backdrop fade in" />
      </div>
    );
  }
}

ModalWindow.propTypes = propTypes;

export default ModalWindow;
