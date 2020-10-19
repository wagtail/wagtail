/* eslint-disable react/prop-types */

import React from 'react';
import { connect } from 'react-redux';

import * as actions from './actions';

import Button from '../../components/Button/Button';
import Icon from '../../components/Icon/Icon';

interface ExplorerToggleProps {
  onToggle(): void;
  children: React.ReactNode;
}

/**
 * A Button which toggles the explorer.
 */
const ExplorerToggle: React.FunctionComponent<ExplorerToggleProps> = ({ children, onToggle }) => (
  <Button
    dialogTrigger={true}
    onClick={onToggle}
  >
    <Icon name="folder-open-inverse" className="icon--menuitem" />
    {children}
    <Icon name="arrow-right" className="icon--submenu-trigger" />
  </Button>
);

const mapStateToProps = () => ({});

const mapDispatchToProps = (dispatch) => ({
  onToggle: (page) => dispatch(actions.toggleExplorer(page)),
});

const mergeProps = (_stateProps, dispatchProps, ownProps) => ({
  children: ownProps.children,
  onToggle: dispatchProps.onToggle.bind(null, ownProps.startPage),
});

export default connect(mapStateToProps, mapDispatchToProps, mergeProps)(ExplorerToggle);
