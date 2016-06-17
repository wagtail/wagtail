import React, { Component, PropTypes } from 'react';

import { ADMIN_PAGES } from 'config';
import Icon from 'components/icon/Icon';
import PublishStatus from 'components/publish-status/PublishStatus';
import PublishedTime from 'components/published-time/PublishedTime';
import StateIndicator from 'components/state-indicator/StateIndicator';

export default class ExplorerItem extends Component {

  constructor(props) {
    super(props);
    this._loadChildren = this._loadChildren.bind(this);
  }

  _humanType(type) {
    let part = type.split('.')[1]
    return part.replace(/([A-Z])/g, ' $1').trim();
  }

  _onNavigate(id) {
    window.location.href = `${ADMIN_PAGES}${id}`;
  }

  _loadChildren(e) {
    e.stopPropagation();
    let { onItemClick, data } = this.props;
    onItemClick(data.id, data.title);
  }

  render() {
    const { title, data, index } = this.props;
    const { meta } = data;
    const typeName = this._humanType(meta.type);

    let count = meta.children.count;

    // TODO refactor.
    // If we only want pages with children, get this info by
    // looking at the descendants count vs children count.
    if (this.props.filter && this.props.filter.match(/has_children/)) {
      count = meta.descendants.count - meta.children.count;
    }

    return (
      <div onClick={this._onNavigate.bind(this, data.id)} className="c-explorer__item">
        {count > 0 ?
        <span className="c-explorer__children" onClick={this._loadChildren}>
          <Icon name="folder-inverse" />
          <span aria-role='presentation'>
            See Children
          </span>
        </span> : null }
        <h3 className="c-explorer__title">
          <StateIndicator state={data.state} />
          {title}
        </h3>
        <p className='c-explorer__meta'>
          {typeName} | <PublishedTime publishedAt={meta.first_published_at} /> | <PublishStatus status={meta.status} />
        </p>
      </div>
    );
  }
}

ExplorerItem.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object
};
