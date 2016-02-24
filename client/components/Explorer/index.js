import React, { Component, PropTypes } from 'react';


export default class Explorer extends Component {

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
      return null;
    }

    const items = cursor.pages.map(item => {
      <div className='explorer__item' key={item.id}>
        {item.title}
      </div>
    });

    return items;
  }

  render() {
    const pages = this._getPages(this.state.cursor);
    return (
      <div className='explorer'>
        Explorer!
        {pages}
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
