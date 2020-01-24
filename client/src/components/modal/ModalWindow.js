import React from 'react';
import FocusTrap from 'react-focus-trap';
import PropTypes from 'prop-types';
import _ from 'lodash';

import ModalHeader from './ModalHeader';

const propTypes = {
  heading: PropTypes.string.isRequired,
  onSearch: PropTypes.func,
  searchEnabled: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onKeyDown: PropTypes.func,
};

class ModalWindow extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      id: _.uniqueId('react-modal-'),
    };
  }

  componentDidMount() {
    // Save the currently focused element so we can reset it when the modal closes
    this.previousFocusedElement = document.activeElement;

    // Focus the search box
    document.getElementById(`${this.state.id}-search`).focus();

    // Close the window when Escape key is pressed
    this.keydownEventListener = e => {
      // Check for custom keydown event handler
      if (this.props.onKeyDown) {
        this.props.onKeyDown(e);

        if (e.defaultPrevented) {
          return;
        }
      }

      // Close modal on click escape
      if (e.key === 'Escape') {
        // Refocus the element that was focused when the modal was opened
        this.previousFocusedElement.focus();

        this.props.onClose(e);
      }
    };
    document.addEventListener('keydown', this.keydownEventListener);
  }

  componentWillUnmount() {
    document.removeEventListener('keydown', this.keydownEventListener);
  }

  render() {
    const onClose = e => {
      // Refocus the element that was focused when the modal was opened
      this.previousFocusedElement.focus();

      this.props.onClose(e);
    };

    return (
      <div>
        <div
          className="modal fade in"
          tabIndex={-1}
          role="dialog"
          aria-modal={true}
          style={{ display: 'block' }}
          aria-labelledby={`${this.state.id}-title`}
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
                    heading={this.props.heading}
                    headingId={`${this.state.id}-title`}
                    searchId={`${this.state.id}-search`}
                    onSearch={this.props.onSearch}
                    searchEnabled={this.props.searchEnabled}
                  />

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
