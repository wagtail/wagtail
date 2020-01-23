import React from 'react';
import PropTypes from 'prop-types';
import _ from 'lodash';

const propTypes = {
  onModalClose: PropTypes.func.isRequired,
};

class ModalWindow extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      id: _.uniqueId('react-modal-'),
    };
  }

  componentWillMount() {
    // Save the currently focused element so we can reset it when the modal closes
    this.previousFocusedElement = document.activeElement;
  }

  // eslint-disable-next-line class-methods-use-this
  renderModalContents() {
    return (
      <div>Empty</div>
    );
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
          aria-labelledby={`${this.state.id}-title`}
          style={{ display: 'block' }}
        >
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
                {this.renderModalContents()}
              </div>
            </div>
          </div>
        </div>
        <div className="modal-backdrop fade in" />
      </div>
    );
  }
}

ModalWindow.propTypes = propTypes;

export default ModalWindow;
