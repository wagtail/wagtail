/* eslint-disable react/prop-types */

import React from 'react';
import styled, { css } from 'styled-components';
import { ModuleDefinition } from '../Sidebar';

interface LogoWrapperProps {
    collapsed: boolean;
}

const LogoWrapper = styled.a<LogoWrapperProps>`
    display: block;
    align-items: center;
    color: #aaa;
    -webkit-font-smoothing: auto;
    position: relative;
    display: block;
    margin: 2em auto;
    text-align: center;
    padding: 10px 0px;
    transition: padding 0.3s ease;

    &:hover {
        color: $color-white;
    }

    ${(props) => props.collapsed && css`
        padding: 40px 0px;
    `}
`;

interface LogoProps {
    homeUrl: string;
    html: string;
    collapsed: boolean;
    navigate(url: string): void;
}

export const Logo: React.FunctionComponent<LogoProps> = ({ homeUrl, html, collapsed, navigate }) => {
  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(homeUrl);
  };

  return (  // GETTEXT
    <LogoWrapper
      collapsed={collapsed}
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
      return <Logo homeUrl={this.homeUrl} html={this.html} collapsed={collapsed} navigate={navigate} />;
    }
}
