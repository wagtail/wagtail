import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Icon } from 'draftail';

import Tooltip from '../Tooltip/Tooltip';
import Portal from '../../Portal/Portal';

/**
 * Shortens the given label if it goes beyond a predetermined limit.
 */
export const shortenLabel = (label) => {
  let shortened = label;
  if (shortened.length > 25) {
    shortened = `${shortened.slice(0, 20)}…`;
  }

  return shortened;
};

const ENTER_KEY_CODE = 13;

class TooltipEntity extends Component {
  constructor(props) {
    super(props);

    this.state = {
      showTooltipAt: null,
    };

    this.onEdit = this.onEdit.bind(this);
    this.onRemove = this.onRemove.bind(this);
    this.openTooltip = this.openTooltip.bind(this);
    this.closeTooltip = this.closeTooltip.bind(this);
  }

  onEdit(e) {
    const { onEdit, entityKey } = this.props;

    e.preventDefault();
    e.stopPropagation();
    onEdit(entityKey);
  }

  onRemove(e) {
    const { onRemove, entityKey } = this.props;

    e.preventDefault();
    e.stopPropagation();
    onRemove(entityKey);
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
      },
    });
  }

  closeTooltip() {
    this.setState({ showTooltipAt: null });
  }

  render() {
    const { children, icon, label, url } = this.props;
    const { showTooltipAt } = this.state;

    return (
      <a
        href={url}
        role="button"
        // Use onMouseUp to preserve focus in the text even after clicking.
        onMouseUp={this.openTooltip}
        className="TooltipEntity"
        data-draftail-trigger
      >
        <Icon icon={icon} className="TooltipEntity__icon" />
        {children}
        {showTooltipAt && (
          <Portal
            node={showTooltipAt.container}
            onClose={this.closeTooltip}
            closeOnClick
            closeOnType
            closeOnResize
          >
            <Tooltip target={showTooltipAt} direction="top">
              {label ? (
                <a
                  href={url}
                  title={url}
                  target="_blank"
                  rel="noreferrer"
                  className="Tooltip__link"
                  onKeyDown={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (e?.keyCode === ENTER_KEY_CODE) {
                      window.open(url, '_blank', 'noopener,noreferrer');
                      this.closeTooltip();
                    }
                  }}
                >
                  {shortenLabel(label)}
                </a>
              ) : null}

              <button
                className="button button-small Tooltip__button"
                onClick={this.onEdit}
                onKeyDown={(e) => {
                  if (e?.keyCode === ENTER_KEY_CODE) this.onEdit(e);
                }}
              >
                Edit
              </button>

              <button
                className="button button-small button-secondary no Tooltip__button"
                onClick={this.onRemove}
                onKeyDown={(e) => {
                  if (e?.keyCode === ENTER_KEY_CODE) this.onRemove(e);
                }}
              >
                Remove
              </button>
            </Tooltip>
          </Portal>
        )}
      </a>
    );
  }
}

TooltipEntity.propTypes = {
  entityKey: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  onEdit: PropTypes.func.isRequired,
  onRemove: PropTypes.func.isRequired,
  icon: PropTypes.oneOfType([
    PropTypes.string.isRequired,
    PropTypes.object.isRequired,
  ]).isRequired,
  label: PropTypes.string.isRequired,
  url: PropTypes.string,
};

TooltipEntity.defaultProps = {
  url: null,
};

export default TooltipEntity;
