/* eslint-disable react/prop-types */

import React from 'react';
import { ModuleDefinition } from '../Sidebar';

interface CustomBrandingProps {
    homeUrl: string;
    html: string;
    collapsed: boolean;
    navigate(url: string): void;
}

const CustomBranding: React.FunctionComponent<CustomBrandingProps> = ({ homeUrl, html, navigate }) => {
  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(homeUrl);
  };

  return (  // GETTEXT
    <a
      className="sidebar-custom-branding"
      href="#"
      onClick={onClick}
      aria-label={'Dashboard'}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export class CustomBrandingModuleDefinition implements ModuleDefinition {
    homeUrl: string;
    html: string;
    collapsible: boolean;  // TODO

    constructor(homeUrl: string, html: string, collapsible: boolean) {
      this.homeUrl = homeUrl;
      this.html = html;
      this.collapsible = collapsible;
    }

    render({ collapsed, navigate }) {
      return <CustomBranding homeUrl={this.homeUrl} html={this.html} collapsed={collapsed} navigate={navigate} />;
    }
}
