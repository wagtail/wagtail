import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Icon } from 'draftail';

import Tooltip from '../Tooltip/Tooltip';
import Portal from '../../Portal/Portal';

// Constraints the maximum size of the tooltip.
const OPTIONS_MAX_WIDTH = 300;
const OPTIONS_SPACING = 70;
const TOOLTIP_MAX_WIDTH = OPTIONS_MAX_WIDTH + OPTIONS_SPACING;

/**
 * Editor block to preview and edit images.
 */
class MediaBlock extends Component {
  constructor(props) {
    super(props);

    this.state = {
      showTooltipAt: null,
    };

    this.openTooltip = this.openTooltip.bind(this);
    this.closeTooltip = this.closeTooltip.bind(this);
    this.renderTooltip = this.renderTooltip.bind(this);
  }

  openTooltip(e) {
    const trigger = e.target.closest('[data-draftail-trigger]');

    // Click is within the tooltip.
    if (!trigger) {
      return;
    }

    const container = trigger.closest('[data-draftail-editor-wrapper]');
    const containerRect = container.getBoundingClientRect();
    const rect = trigger.getBoundingClientRect();
    const maxWidth = trigger.parentNode.offsetWidth - rect.width;

    this.setState({
      showTooltipAt: {
        container: container,
        top: rect.top - containerRect.top - (document.documentElement.scrollTop || document.body.scrollTop),
        left: rect.left - containerRect.left - (document.documentElement.scrollLeft || document.body.scrollLeft),
        width: rect.width,
        height: rect.height,
        direction: maxWidth >= TOOLTIP_MAX_WIDTH ? 'left' : 'top-left',
      },
    });
  }

  closeTooltip() {
    this.setState({ showTooltipAt: null });
  }

  renderTooltip() {
    const { children } = this.props;
    const { showTooltipAt } = this.state;

    return (
      <Portal
        node={showTooltipAt.container}
        onClose={this.closeTooltip}
        closeOnClick
        closeOnType
        closeOnResize
      >
        <Tooltip target={showTooltipAt} direction={showTooltipAt.direction}>
          <div style={{ maxWidth: OPTIONS_MAX_WIDTH }}>{children}</div>
        </Tooltip>
      </Portal>
    );
  }

  render() {
    const { blockProps, src, alt } = this.props;
    const { showTooltipAt } = this.state;
    const { entityType } = blockProps;

    return (
      <button
        type="button"
        tabIndex={-1}
        className="MediaBlock"
        onClick={this.openTooltip}
        data-draftail-trigger
      >
        <span className="MediaBlock__icon-wrapper" aria-hidden>
          <Icon icon={entityType.icon} className="MediaBlock__icon" />
        </span>

        <img className="MediaBlock__img" src={src} alt={alt} width="256" />

        {showTooltipAt && this.renderTooltip()}
      </button>
    );
  }
}

MediaBlock.propTypes = {
  blockProps: PropTypes.shape({
    entityType: PropTypes.object.isRequired,
  }).isRequired,
  src: PropTypes.string,
  alt: PropTypes.string,
  children: PropTypes.node.isRequired,
};

MediaBlock.defaultProps = {
  src: null,
  alt: '',
};

export default MediaBlock;
