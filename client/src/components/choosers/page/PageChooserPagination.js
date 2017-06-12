import React from 'react';
import PropTypes from 'prop-types';

const propTypes = {
  totalPages: PropTypes.number.isRequired,
  pageNumber: PropTypes.number,
  onChangePage: PropTypes.func.isRequired,
};

const defaultProps = {
  pageNumber: 0,
};

class PageChooserPagination extends React.Component {
  renderPrev() {
    const { pageNumber, onChangePage } = this.props;
    const hasPrev = pageNumber !== 1;

    if (hasPrev) {
      const onClickPrevious = (e) => {
        onChangePage(pageNumber - 1);
        e.preventDefault();
      };

      return (
        <li className="prev">
          <a
            onClick={onClickPrevious}
            href="#"
            className="icon icon-arrow-left navigate-pages"
          >
            Previous
          </a>
        </li>
      );
    } else {
      return (
        <li className="prev" />
      );
    }
  }

  renderNext() {
    const { pageNumber, onChangePage, totalPages } = this.props;
    const hasNext = pageNumber < totalPages;

    if (hasNext) {
      const onClickNext = (e) => {
        onChangePage(pageNumber + 1);
        e.preventDefault();
      };

      return (
        <li className="next">
          <a
            onClick={onClickNext}
            href="#"
            className="icon icon-arrow-right-after navigate-pages"
          >
            Next
          </a>
        </li>
      );
    } else {
      return (
        <li className="next" />
      );
    }
  }

  render() {
    const { totalPages, pageNumber } = this.props;

    return (
      <div className="pagination">
        {totalPages > 1 ? (
          <div>
            <p>
              {`Page ${pageNumber} of ${totalPages}.`}
            </p>
            <ul>
              {this.renderPrev()}
              {this.renderNext()}
            </ul>
          </div>
        ) : null}
      </div>
    );
  }
}

PageChooserPagination.propTypes = propTypes;
PageChooserPagination.defaultProps = defaultProps;

export default PageChooserPagination;
