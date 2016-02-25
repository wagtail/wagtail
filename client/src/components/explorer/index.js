import React, { Component, PropTypes } from 'react';
import LoadingIndicator from '../loading-indicator';

import ExplorerItem from './explorer-item';

class Explorer extends Component {

  constructor(props) {
    super(props);

    this.state = { cursor: null };
  }

  componentDidMount() {
    fetch('/api/v1/pages/?child_of=2')
    .then(res => { return res.json() })
    .then(body => {
      this.setState({
        cursor: body
      });
    });
  }

  componentWillUnmount(cursor) {

  }

  _getPages(cursor) {
    if (!cursor) {
      return [];
    }

    return cursor.pages.map(item =>
      <ExplorerItem key={item.id} title={item.title} data={item} />
    );
  }

  render() {
    const { cursor } = this.state;
    const pages = this._getPages(cursor);

    return (
      <div className="c-explorer">
        {cursor ? pages : <LoadingIndicator />}
      </div>
    );
  }
}

Explorer.propTypes = {
  onPageSelect: PropTypes.func,
  initialPath: PropTypes.string,
  apiPath: PropTypes.string,
  size: PropTypes.number
};

export default Explorer;
