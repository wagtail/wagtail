import React from 'react';

import PageChooserResultSet from '../PageChooserResultSet';


export default class PageChooserBrowseView extends React.Component {
  renderTitle() {
    switch (this.props.totalItems) {
      case 0:
        return "There are no matches"
      case 1:
        return "There is 1 match"
      default:
        return `There are ${this.props.totalItems} matches`
    }
  }

  render() {
    return <div className="nice-padding">
      <h2>{this.renderTitle()}</h2>
      <PageChooserResultSet pageNumber={this.props.pageNumber} totalPages={this.props.totalPages} items={this.props.items} pageTypes={this.props.pageTypes} restrictPageTypes={this.props.restrictPageTypes} onPageChosen={this.props.onPageChosen} onNavigate={this.props.onNavigate} onChangePage={this.props.onChangePage} />
    </div>;
  }
}
