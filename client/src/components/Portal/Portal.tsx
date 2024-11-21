/* eslint-disable react/static-property-placement */
import PropTypes from 'prop-types';
import { Component } from 'react';
import { createPortal } from 'react-dom';

/**
 * A Portal component which automatically closes itself
 * when certain events happen outside.
 * See https://reactjs.org/docs/portals.html.
 */
class Portal extends Component<{
  closeOnClick: boolean;
  closeOnResize: boolean;
  closeOnType: boolean;
  node: Element;
  onClose: () => void;
}> {
  static propTypes = {
    onClose: PropTypes.func.isRequired,
    node: PropTypes.instanceOf(Element),
    children: PropTypes.node,
    closeOnClick: PropTypes.bool,
    closeOnType: PropTypes.bool,
    closeOnResize: PropTypes.bool,
  };

  static defaultProps = {
    node: document.body,
    children: null,
    closeOnClick: false,
    closeOnType: false,
    closeOnResize: false,
  };

  portal: HTMLElement;
  CONTROL_KEY_CODE: number = 17;
  K_KEY_CODE: number = 75
  ENTER_KEY_CODE: number = 13

  constructor(props) {
    super(props);

    this.portal = document.createElement('div');

    this.onCloseEvent = this.onCloseEvent.bind(this);
  }

  onCloseEvent(event: MouseEvent) {
    const isLinkTooltipKeyTriggerEvent = this.checkTooltipKeyTriggerEvent(event);

    if(!isLinkTooltipKeyTriggerEvent){
      const { onClose } = this.props;
      const target = event.target as Element;

      if (!this.portal.contains(target)) {
        onClose();
      }
    }
  }

  checkTooltipKeyTriggerEvent(event: MouseEvent | KeyboardEvent){
    if(event instanceof KeyboardEvent){
      if(event?.ctrlKey && event?.keyCode === this.K_KEY_CODE) return true
      if([this.CONTROL_KEY_CODE, this.K_KEY_CODE, this.ENTER_KEY_CODE].includes(event?.keyCode)) return true
    }
    return false
  }

  componentDidMount() {
    const { node, onClose, closeOnClick, closeOnType, closeOnResize } =
      this.props;

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

export default Portal;
