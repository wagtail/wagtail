import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const getEmailAddress = mailto => mailto.replace('mailto:', '').split('?')[0];
const getDomainName = url => url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

const linkIcon = <Icon name="link" />;
const mailIcon = <Icon name="mail" />;

const Link = props => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();
  let icon;
  let label;

  if (data.id) {
    icon = linkIcon;
    label = data.url;
  } else if (data.url.startsWith('mailto:')) {
    icon = mailIcon;
    label = getEmailAddress(data.url);
  } else {
    icon = linkIcon;
    label = getDomainName(data.url);
  }

  return (
    <TooltipEntity
      {...props}
      icon={icon}
      label={label}
      url={data.url}
    />
  );
};

Link.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Link;
