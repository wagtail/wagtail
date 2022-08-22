import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Icon } from 'draftail';

import { SelectionState, EditorState } from 'draft-js';
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

    this.onClick = this.onClick.bind(this);
    this.selectCurrentBlock = this.selectCurrentBlock.bind(this);
    this.openTooltip = this.openTooltip.bind(this);
    this.closeTooltip = this.closeTooltip.bind(this);
    this.renderTooltip = this.renderTooltip.bind(this);
  }

  onClick(e) {
    const trigger = e.target.closest('[data-draftail-trigger]');

    // Click is within the tooltip.
    if (!trigger) {
      return;
    }

    this.selectCurrentBlock();
    this.openTooltip(trigger);
  }

  selectCurrentBlock() {
    const { block, blockProps } = this.props;
    const { editorState, onChange } = blockProps;
    const selection = new SelectionState({
      anchorKey: block.getKey(),
      anchorOffset: 0,
      focusKey: block.getKey(),
      focusOffset: block.getLength(),
      hasFocus: true,
    });
    onChange(EditorState.forceSelection(editorState, selection));
  }

  openTooltip(trigger) {
    const container = trigger.closest('[data-draftail-editor-wrapper]');
    const containerRect = container.getBoundingClientRect();
    const rect = trigger.getBoundingClientRect();
    const maxWidth = trigger.parentNode.offsetWidth - rect.width;

    this.setState({
      showTooltipAt: {
        container: container,
        top:
          rect.top -
          containerRect.top -
          (document.documentElement.scrollTop || document.body.scrollTop),
        left:
          rect.left -
          containerRect.left -
          (document.documentElement.scrollLeft || document.body.scrollLeft),
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
    const { blockProps, src, alt, fallbackText } = this.props;
    const { showTooltipAt } = this.state;
    const { entityType } = blockProps;

    return (
      <button
        type="button"
        tabIndex={-1}
        className="MediaBlock"
        onClick={this.onClick}
        data-draftail-trigger
      >
        <span className="MediaBlock__icon-wrapper" aria-hidden>
          <Icon icon={entityType.icon} className="MediaBlock__icon" />
        </span>
        <img className="MediaBlock__img" src={src} alt={alt} width="256" />

        {src ? null : (
          <span className="MediaBlock__fallback">{fallbackText}</span>
        )}
        {showTooltipAt && this.renderTooltip()}
      </button>
    );
  }
}

MediaBlock.propTypes = {
  blockProps: PropTypes.shape({
    entityType: PropTypes.object.isRequired,
    editorState: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
  }).isRequired,
  block: PropTypes.object.isRequired,
  src: PropTypes.string,
  alt: PropTypes.string,
  fallbackText: PropTypes.string,
  children: PropTypes.node.isRequired,
};

MediaBlock.defaultProps = {
  src: null,
  alt: '',
  fallbackText: null,
};

export default MediaBlock;
