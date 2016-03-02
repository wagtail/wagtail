import React, { Component, PropTypes } from 'react';
import moment from 'moment';


const PublishTime = ({publishedAt}) => {
  let date = moment(publishedAt);
  let str = publishedAt ?  date.format('DD.MM.YYYY') : 'No date';

  return (
    <span>{str}</span>
  );
}

export default PublishTime;
