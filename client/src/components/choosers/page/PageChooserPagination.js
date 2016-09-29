import React from 'react';


export default class PageChooserPagination extends React.Component {
  renderPrev() {
    let hasPrev = this.props.pageNumber != 1;

    if (hasPrev) {
      let onClickPrevious = (e) => {
        this.props.onChangePage(this.props.pageNumber - 1);
        e.preventDefault();
      };

      return <li className="prev">
        <a onClick={onClickPrevious} href="#" className="icon icon-arrow-left navigate-pages">Previous</a>
      </li>;
    } else {
      return <li className="prev"></li>;
    }
  }

  renderNext() {
    let hasNext = this.props.pageNumber < this.props.totalPages;

    if (hasNext) {
      let onClickNext = (e) => {
        this.props.onChangePage(this.props.pageNumber + 1);
        e.preventDefault();
      };

      return <li className="next">
        <a onClick={onClickNext} href="#" className="icon icon-arrow-right-after navigate-pages">Next</a>
      </li>;
    } else {
      return <li className="next"></li>;
    }
  }

  render() {
    if (this.props.totalPages > 1) {
      return <div className="pagination">
        <p>
          {`Page ${this.props.pageNumber} of ${this.props.totalPages}.`}
        </p>
        <ul>
          {this.renderPrev()}
          {this.renderNext()}
        </ul>
      </div>;
    } else {
      return <div className="pagination"></div>;
    }
  }
}
