import React from 'react';

import PageChooserResultSet from '../PageChooserResultSet';


export default class PageChooserBrowseView extends React.Component {
  renderBreadcrumb() {
    let breadcrumbItems = [];

    if (this.props.parentPage) {
      let ancestorPages = this.props.parentPage.meta.ancestors;

      for (let ancestorPage of ancestorPages) {
        let onNavigate = (e) => {
          this.props.onNavigate(ancestorPage);
          e.preventDefault();
        }

        if (ancestorPage.id == 1) {
          breadcrumbItems.push(<li key={ancestorPage.id} className="home"><a onClick={onNavigate} href="#" className="navigate-pages icon icon-home text-replace">Home</a></li>);
        } else {
          breadcrumbItems.push(<li key={ancestorPage.id}><a onClick={onNavigate} href="#" className="navigate-pages">{ancestorPage.title}</a></li>);
        }
      }
    }

    return <ul className="breadcrumb">{breadcrumbItems}</ul>;
  }
  render() {
    return <div className="nice-padding">
      <h2>Explorer</h2>
      {this.renderBreadcrumb()}
      <PageChooserResultSet pageNumber={this.props.pageNumber} totalPages={this.props.totalPages} parentPage={this.props.parentPage} items={this.props.items} pageTypes={this.props.pageTypes} restrictPageTypes={this.props.restrictPageTypes} displayChildNavigation={true} onPageChosen={this.props.onPageChosen} onNavigate={this.props.onNavigate} onChangePage={this.props.onChangePage} />
    </div>;
  }
}
