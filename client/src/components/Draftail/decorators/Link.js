import PropTypes from 'prop-types';
import React from 'react';

import Icon from '../../Icon/Icon';

import TooltipEntity from '../decorators/TooltipEntity';

const getEmailAddress = mailto => mailto.replace('mailto:', '').split('?')[0];
const getDomainName = url => url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

const Link = props => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();
  let icon;
  let label;
  let tooltipURL;

  if (data.id) {
    icon = 'link';
    tooltipURL = data.url;
    label = data.url;
  } else if (data.url.startsWith('mailto:')) {
    icon = 'mail';
    tooltipURL = getEmailAddress(data.url);
    label = data.url;
  } else {
    icon = 'link';
    tooltipURL = data.url;
    label = getDomainName(data.url);
  }

  return (
    <TooltipEntity
      {...props}
      icon={<Icon name={icon} />}
      label={label}
      url={tooltipURL}
    />
  );
};

Link.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Link;
