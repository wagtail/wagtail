import React from 'react';
import moment from 'moment';

import { DATE_FORMAT, STRINGS } from '../../config/wagtail';

const AbsoluteDate = ({ time }) => {
  const date = moment(time);
  const text = time ?  date.format(DATE_FORMAT) : STRINGS.NO_DATE;

  return (
    <span>{text}</span>
  );
};

AbsoluteDate.propTypes = {
  time: React.PropTypes.string,
};

AbsoluteDate.defaultProps = {
  time: '',
};

export default AbsoluteDate;
