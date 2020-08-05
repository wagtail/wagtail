import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

import { STRINGS } from '../../../config/wagtailConfig';

const LINK_ICON = <Icon name="link" />;
const BROKEN_LINK_ICON = <Icon name="warning" />;
const MAIL_ICON = <Icon name="mail" />;

const getEmailAddress = mailto => mailto.replace('mailto:', '').split('?')[0];
const getPhoneNumber = tel => tel.replace('tel:', '').split('?')[0];
const getDomainName = url => url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

// Determines how to display the link based on its type: page, mail, anchor or external.
export const getLinkAttributes = (data) => {
  const url = data.url || null;
  let icon;
  let label;

  if (!url) {
    icon = BROKEN_LINK_ICON;
    label = STRINGS.BROKEN_LINK;
  } else if (data.id) {
    icon = LINK_ICON;
    label = url;
  } else if (url.startsWith('mailto:')) {
    icon = MAIL_ICON;
    label = getEmailAddress(url);
  } else if (url.startsWith('tel:')) {
    icon = LINK_ICON;
    label = getPhoneNumber(url);
  } else if (url.startsWith('#')) {
    icon = LINK_ICON;
    label = url;
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
