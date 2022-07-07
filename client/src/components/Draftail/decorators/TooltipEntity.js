import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Icon, Tooltip } from 'draftail';

const shortenLabel = (label) => {
  let shortened = label;
  if (shortened.length > 25) {
    shortened = `${shortened.slice(0, 20)}…`;
  }

  return shortened;
};

class TooltipEntity extends Component {
  constructor(props) {
    super(props);

    this.state = {
      showTooltipAt: null,
    };

    this.openTooltip = this.openTooltip.bind(this);
  }

  openTooltip(e) {
    const trigger = e.target.closest('[data-draftail-trigger]');

    // Click is within the tooltip.
    if (!trigger) {
      return;
    }

    this.setState({
      showTooltipAt: trigger.getBoundingClientRect(),
    });
  }

  renderTooltip() {
    const { label, url, onEdit, onRemove, entityKey } = this.props;

    return (
      <div className="Draftail-InlineToolbar" role="toolbar">
        {label ? (
          <a
            href={url}
            title={url}
            target="_blank"
            rel="noreferrer"
            className="Tooltip__link"
          >
            {shortenLabel(label)}
          </a>
        ) : null}

        <button
          type="button"
          className="button Tooltip__button"
          onClick={onEdit.bind(null, entityKey)}
        >
          Edit
        </button>

        <button
          type="button"
          className="button button-secondary no Tooltip__button"
          onClick={onRemove.bind(null, entityKey)}
        >
          Remove
        </button>
      </div>
    );
  }

  render() {
    const { children, icon, url } = this.props;
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
        <Tooltip
          shouldOpen={Boolean(showTooltipAt)}
          onHide={() => this.setState({ showTooltipAt: null })}
          getTargetPosition={(editorRect) => {
            if (!showTooltipAt) {
              return null;
            }

            return {
              left: `calc(${
                showTooltipAt.left - editorRect.left
              }px + var(--draftail-offset-inline-start, 0))`,
              top: 0,
            };
          }}
          content={this.renderTooltip()}
        />
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
