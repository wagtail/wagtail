import PropTypes from 'prop-types';
import React, { Component } from 'react';
import { Icon } from 'draftail';

import Tooltip from '../Tooltip/Tooltip';
import Portal from '../../Portal/Portal';

class TooltipEntity extends Component {
  constructor(props) {
    super(props);

    this.state = {
      showTooltipAt: null,
    };

    this.openTooltip = this.openTooltip.bind(this);
    this.closeTooltip = this.closeTooltip.bind(this);
  }

  openTooltip(e) {
    const trigger = e.target;
    this.setState({ showTooltipAt: trigger.getBoundingClientRect() });
  }

  closeTooltip() {
    this.setState({ showTooltipAt: null });
  }

  render() {
    const {
      entityKey,
      children,
      onEdit,
      onRemove,
      icon,
      label,
      url,
    } = this.props;
    const { showTooltipAt } = this.state;

    // Contrary to what JSX A11Y says, this should be a button but it shouldn't be focusable.
    /* eslint-disable springload/jsx-a11y/interactive-supports-focus */
    return (
      <a role="button" onMouseUp={this.openTooltip} className="TooltipEntity">
        <Icon icon={icon} className="TooltipEntity__icon" />
        {children}
        {showTooltipAt && (
          <Portal
            onClose={this.closeTooltip}
            closeOnClick
            closeOnType
            closeOnResize
          >
            <Tooltip target={showTooltipAt} direction="top">
              <a
                href={url}
                title={url}
                target="_blank"
                rel="noopener noreferrer"
                className="Tooltip__link"
              >
                {label}
              </a>

              <button
                className="button Tooltip__button"
                onClick={onEdit.bind(null, entityKey)}
              >
                Edit
              </button>

              <button
                className="button button-secondary no Tooltip__button"
                onClick={onRemove.bind(null, entityKey)}
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
  url: PropTypes.string.isRequired,
};

export default TooltipEntity;
