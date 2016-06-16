import React, { Component } from 'react';
import { connect } from 'react-redux';

class Toggle extends Component {
  constructor(props) {
    super(props)
    this._sandbox = this._sandbox.bind(this);
  }

  componentDidUpdate() {
    if (this.props.visible) {
      this.refs.btn.addEventListener('click', this._sandbox);
    } else {
      this.refs.btn.removeEventListener('click', this._sandbox);
    }
  }

  _sandbox(e) {
    e.stopPropagation();
    e.preventDefault();
    this.props.onToggle(this.props.page);
  }

  render() {
    const cls = ['icon icon-folder-open-inverse dl-trigger'];

    if (this.props.loading) {
      cls.push('icon-spinner');
    }

    return (
      <a ref="btn" onClick={this._sandbox} className={cls.join('  ')}>
        {this.props.label}
      </a>
    );
  }
}

Toggle.propTypes = {

};

const mapStateToProps = (store) => {
  return {
    loading: store.explorer.isFetching,
    visible: store.explorer.isVisible,
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    onToggle: (id) => {
      dispatch({ type: 'TOGGLE_EXPLORER', id })
    }
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(Toggle);
