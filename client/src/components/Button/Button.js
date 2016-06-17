import React from 'react';
import _ from 'lodash';

/**
 * A reusable button. Uses a <a> tag underneath.
 */
export default React.createClass({
  propTypes: {
    href: React.PropTypes.string,
    className: React.PropTypes.string,
    icon: React.PropTypes.string,
    target: React.PropTypes.string,
    children: React.PropTypes.node,
    accessibleLabel: React.PropTypes.string,
    onClick: React.PropTypes.func,
    isLoading: React.PropTypes.bool,
    preventDefault: React.PropTypes.bool,
  },

  getDefaultProps() {
    return {
      href: '#',
      className: '',
      icon: '',
      target: null,
      children: null,
      accessibleLabel: null,
      onClick: null,
      isLoading: false,
      preventDefault: true,
    };
  },

  handleClick(e) {
    const { href, onClick, preventDefault } = this.props;

    if (preventDefault && href === '#') {
      e.preventDefault();
      e.stopPropagation();
    }

    if (onClick) {
      onClick(e);
    }
  },

  render() {
    const {
      className,
      icon,
      children,
      accessibleLabel,
      isLoading,
      target,
    } = this.props;

    const props = _.omit(this.props, [
      'className',
      'icon',
      'iconClassName',
      'children',
      'accessibleLabel',
      'isLoading',
      'onClick',
      'preventDefault',
    ]);

    const hasIcon = icon !== '';
    const hasText = children !== null;
    const iconName = isLoading ? 'spinner' : icon;
    const accessibleElt = accessibleLabel ? (
      <span className="visuallyhidden">
        {accessibleLabel}
      </span>
    ) : null;

    return (
      <a
        className={`${className} ${hasIcon ? 'icon icon-' : ''}${iconName}`}
        onClick={this.handleClick}
        rel={target === '_blank' ? 'noopener' : null}
        {...props}
      >
        {hasText ? children : accessibleElt}
      </a>
    );
  },
});
