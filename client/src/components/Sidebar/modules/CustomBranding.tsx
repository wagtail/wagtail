/* eslint-disable react/prop-types */

import * as React from 'react';
import { ModuleDefinition } from '../Sidebar';

interface CustomBrandingProps {
  homeUrl: string;
  html: string;
  strings;
  currentPath: string;
  navigate(url: string): void;
}

const CustomBranding: React.FunctionComponent<CustomBrandingProps> = ({
  homeUrl,
  html,
  strings,
  currentPath,
  navigate,
}) => {
  const onClick = (e: React.MouseEvent) => {
    // Do not capture click events with modifier keys or non-main buttons.
    if (
      e.ctrlKey ||
      e.shiftKey ||
      e.metaKey ||
      (e.button && e.button !== 0)
    ) {
      return;
    }

    e.preventDefault();
    navigate(homeUrl);
  };

  return (
    <a
      className="sidebar-custom-branding"
      href={homeUrl}
      onClick={onClick}
      aria-label={strings.DASHBOARD}
      aria-current={currentPath === homeUrl ? 'page' : undefined}
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

  render({ strings, currentPath, navigate, key }) {
    return (<CustomBranding
      key={key}
      homeUrl={this.homeUrl}
      html={this.html}
      strings={strings}
      currentPath={currentPath}
      navigate={navigate}
    />);
  }
}
