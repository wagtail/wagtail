import PropTypes from 'prop-types';
import React, { Component } from 'react';
import ReactDOM from 'react-dom';

class Portal extends Component {
  constructor(props) {
    super(props);

    this.onCloseEvent = this.onCloseEvent.bind(this);
  }

  onCloseEvent(e) {
    const { onClose } = this.props;

    if (!this.portal.contains(e.target)) {
      onClose();
    }
  }

  componentDidMount() {
    const { onClose, closeOnClick, closeOnType, closeOnResize } = this.props;

    if (!this.portal) {
      this.portal = document.createElement('div');
      document.body.appendChild(this.portal);

      if (onClose) {
        if (closeOnClick) {
          document.addEventListener('mouseup', this.onCloseEvent);
        }

        if (closeOnType) {
          document.addEventListener('keyup', this.onCloseEvent);
        }

        if (closeOnResize) {
          window.addEventListener('resize', onClose);
        }
      }
    }

    this.componentDidUpdate();
  }

  componentDidUpdate() {
    const { children } = this.props;

    ReactDOM.render(<div>{children}</div>, this.portal);
  }

  componentWillUnmount() {
    const { onClose } = this.props;

    document.body.removeChild(this.portal);

    document.removeEventListener('mouseup', this.onCloseEvent);
    document.removeEventListener('keyup', this.onCloseEvent);
    window.removeEventListener('resize', onClose);
  }

  render() {
    return null;
  }
}

Portal.propTypes = {
  onClose: PropTypes.func,
  children: PropTypes.node,
  closeOnClick: PropTypes.bool,
  closeOnType: PropTypes.bool,
  closeOnResize: PropTypes.bool,
};

Portal.defaultProps = {
  onClose: null,
  children: null,
  closeOnClick: false,
  closeOnType: false,
  closeOnResize: false,
};

export default Portal;
