import PropTypes from 'prop-types';
import { Component } from 'react';
import { createPortal } from 'react-dom';

/**
 * A Portal component which automatically closes itself
 * when certain events happen outside.
 * See https://reactjs.org/docs/portals.html.
 */
class Portal extends Component {
  constructor(props) {
    super(props);

    this.portal = document.createElement('div');

    this.onCloseEvent = this.onCloseEvent.bind(this);
  }

  onCloseEvent(e) {
    const { onClose } = this.props;

    if (!this.portal.contains(e.target)) {
      onClose();
    }
  }

  componentDidMount() {
    const { node, onClose, closeOnClick, closeOnType, closeOnResize } = this.props;

    node.appendChild(this.portal);

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

  componentWillUnmount() {
    const { node, onClose } = this.props;

    node.removeChild(this.portal);

    document.removeEventListener('mouseup', this.onCloseEvent);
    document.removeEventListener('keyup', this.onCloseEvent);
    window.removeEventListener('resize', onClose);
  }

  render() {
    const { children } = this.props;

    return createPortal(children, this.portal);
  }
}

Portal.propTypes = {
  onClose: PropTypes.func.isRequired,
  node: PropTypes.instanceOf(Element),
  children: PropTypes.node,
  closeOnClick: PropTypes.bool,
  closeOnType: PropTypes.bool,
  closeOnResize: PropTypes.bool,
};

Portal.defaultProps = {
  node: document.body,
  children: null,
  closeOnClick: false,
  closeOnType: false,
  closeOnResize: false,
};

export default Portal;
