import React, { Component, PropTypes } from 'react';

import { ADMIN_PAGES, STRINGS } from 'config';
import Icon from 'components/icon/Icon';
import PublishStatus from 'components/publish-status/PublishStatus';
import PublishedTime from 'components/published-time/PublishedTime';

export default class ExplorerItem extends Component {

  constructor(props) {
    super(props);
    this._loadChildren = this._loadChildren.bind(this);
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
    const { title, typeName, data, index } = this.props;
    const { meta } = data;

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
          <Icon name="folder-inverse" title={STRINGS.SEE_CHILDREN} />
        </span> : null }
        <h3 className="c-explorer__title">
          {title}
        </h3>
        <p className='c-explorer__meta'>
          <span className="c-explorer__meta__type">{typeName}</span> | <PublishedTime publishedAt={meta.latest_revision_created_at} /> | <PublishStatus status={meta.status} />
        </p>
      </div>
    );
  }
}

ExplorerItem.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object
};
