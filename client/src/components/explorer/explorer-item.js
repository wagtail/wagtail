import React, { Component, PropTypes } from 'react';
import StateIndicator from 'components/state-indicator';
import moment from 'moment';


const PublishTime = ({publishedAt}) => {
  let date = moment(publishedAt);
  let str = publishedAt ?  date.format('DD.MM.YYYY') : 'No date';
  return (
    <span>{str}</span>
  );
}

const PublishStatus = ({ status }) => {
  if (!status) {
    return null;
  }

  let classes = ['o-pill', 'c-status', 'c-status--' + status.status];

  return (
    <span className={classes.join('  ')}>
      {status.status}
    </span>
  );
}


export default class ExplorerItem extends Component {

  _humanType(type) {
    let part = type.split('.')[1]
    return part.replace(/([A-Z])/g, ' $1').trim();
  }

  _onNavigate(id) {
    window.location.href = `/admin/pages/${id}`;
  }

  _onChildren(e) {
    e.stopPropagation();
    let { onItemClick, data } = this.props;
    onItemClick(data.id);
  }

  render() {
    const { title, data } = this.props;


    return (
      <div onClick={this._onNavigate.bind(this, data.id)} className="c-explorer__item">
        {data.meta.children.count > 0 ?
        <span className="c-explorer__children" onClick={this._onChildren.bind(this)}>
          <span className="icon icon-folder-inverse"></span>
          <span aria-role='presentation'>
            Children
          </span>
        </span>  : null }
        <h3 className="c-explorer__title">
          <StateIndicator state={data.state} />
          {title}
        </h3>
        <p className='c-explorer__meta'>
          {this._humanType(data.meta.type)} | <PublishTime publishedAt={data.meta.first_published_at}   /> <PublishStatus status={data.meta.status} />
        </p>
      </div>
    );
  }
}


ExplorerItem.propTypes = {
  title: PropTypes.string,
  data: PropTypes.object
};
