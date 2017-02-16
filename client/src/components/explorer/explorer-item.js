import React, { Component, PropTypes } from 'react';
import StateIndicator from 'components/state-indicator';

export default class ExplorerItem extends Component {
  constructor(props) {
    super(props);
    this.state = {};
  }

  render() {
    const { title, data } = this.props;

    return (
      <div className="c-explorer__item">
        <h3 className="c-explorer__title">
          <StateIndicator state={data.state} />
          {title}
        </h3>
      </div>
    );
  }
}


ExplorerItem.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object
};
