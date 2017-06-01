import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';

import Button from '../../components/Button/Button';

/**
 * A Button which toggles the explorer.
 */
const ExplorerToggle = ({ children, onToggle }) => (
  <Button
    icon={['folder-open-inverse', 'arrow-right-after']}
    onClick={onToggle}
  >
    {children}
  </Button>
);

ExplorerToggle.propTypes = {
  onToggle: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
};

const mapStateToProps = () => ({});

const mapDispatchToProps = (dispatch) => ({
  onToggle: (page) => dispatch(actions.toggleExplorer(page)),
});

const mergeProps = (stateProps, dispatchProps, ownProps) => ({
  children: ownProps.children,
  onToggle: dispatchProps.onToggle.bind(null, ownProps.startPage),
});

export default connect(mapStateToProps, mapDispatchToProps, mergeProps)(ExplorerToggle);
