import React from 'react';

import { ADMIN_PAGES } from 'config';

const PageCount = ({ id, count }) => {
  let prefix = '';
  let suffix = 'pages';

  if (count === 0) {
    return <div />;
  }

  if (count > 1) {
    prefix = 'all ';
  }

  if (count === 1) {
    suffix = 'page';
  }

  return (
    <div onClick={() => {
        window.location.href = `${ADMIN_PAGES}${id}/`
      }}
      className="c-explorer__see-more">
      See {prefix}{ count } {suffix}
    </div>
  );
}

export default PageCount;
