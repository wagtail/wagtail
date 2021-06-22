/* eslint-disable react/prop-types */

import * as React from 'react';
import { ModuleDefinition } from '../Sidebar';

interface CustomBrandingProps {
  homeUrl: string;
  html: string;
  strings;
  navigate(url: string): void;
}

const CustomBranding: React.FunctionComponent<CustomBrandingProps> = ({ homeUrl, html, strings, navigate }) => {
  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(homeUrl);
  };

  return (
    <a
      className="sidebar-custom-branding"
      href="#"
      onClick={onClick}
      aria-label={strings.DASHBOARD}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

export class CustomBrandingModuleDefinition implements ModuleDefinition {
  homeUrl: string;
  html: string;

  constructor(homeUrl: string, html: string) {
    this.homeUrl = homeUrl;
    this.html = html;
  }

  render({ strings, navigate, key }) {
    return <CustomBranding key={key} homeUrl={this.homeUrl} html={this.html} strings={strings} navigate={navigate} />;
  }
}
