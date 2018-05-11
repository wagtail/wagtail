import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const LINK_ICON = <Icon name="link" />;
const MAIL_ICON = <Icon name="mail" />;

const getEmailAddress = mailto => mailto.replace('mailto:', '').split('?')[0];
const getDomainName = url => url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

// Determines how to display the link based on its type: page, mail, or external.
export const getLinkAttributes = (data) => {
  const url = data.url || '';
  let icon;
  let label;

  if (data.id) {
    icon = LINK_ICON;
    label = url;
  } else if (url.startsWith('mailto:')) {
    icon = MAIL_ICON;
    label = getEmailAddress(url);
  } else {
    icon = LINK_ICON;
    label = getDomainName(url);
  }

  return {
    url,
    icon,
    label,
  };
};

/**
 * Represents a link within the editor's content.
 */
const Link = props => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();

  return (
    <TooltipEntity
      {...props}
      {...getLinkAttributes(data)}
    />
  );
};

Link.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Link;
