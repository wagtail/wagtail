import React from 'react';

const ADMIN_URL = '/admin/pages/';

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
        window.location.href = `${ADMIN_URL}${id}/`
      }}
      className="c-explorer__see-more">
      See {prefix}{ count } {suffix}
    </div>
  );
}

export default PageCount;
