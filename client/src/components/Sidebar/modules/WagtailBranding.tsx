/* eslint-disable react/prop-types */

import * as React from 'react';
import { ModuleDefinition, Strings } from '../Sidebar';

export interface LogoImages {
  mobileLogo: string;
  desktopLogoBody: string
  desktopLogoTail: string;
  desktopLogoEyeOpen: string;
  desktopLogoEyeClosed: string;
}

interface WagtailBrandingProps {
  homeUrl: string;
  images: LogoImages;
  strings: Strings;
  navigate(url: string): void;
}

const WagtailBranding: React.FunctionComponent<WagtailBrandingProps> = ({ homeUrl, images, strings, navigate }) => {
  // Tail wagging
  // If the pointer changes direction 8 or more times without leaving, wag the tail!
  const lastMouseX = React.useRef(0);
  const lastDir = React.useRef<'r' | 'l'>('r');
  const dirChangeCount = React.useRef(0);
  const [isWagging, setIsWagging] = React.useState(false);


  const onClick = (e: React.MouseEvent) => {
    e.preventDefault();
    navigate(homeUrl);
  };

  const onMouseMove = (e: React.MouseEvent) => {
    const mouseX = e.pageX;
    const dir: 'r' | 'l' = (mouseX > lastMouseX.current) ? 'r' : 'l';

    if (mouseX !== lastMouseX.current && dir !== lastDir.current) {
      dirChangeCount.current += 1;
    }

    if (dirChangeCount.current > 8) {
      setIsWagging(true);
    }

    lastMouseX.current = mouseX;
    lastDir.current = dir;
  };

  const onMouseLeave = () => {
    setIsWagging(false);
    dirChangeCount.current = 0;
  };

  const desktopClassName = (
    'sidebar-wagtail-branding'
    + (isWagging ? ' sidebar-wagtail-branding--wagging' : '')
  );

  return (
    <a
      className={desktopClassName} href="#" aria-label={strings.DASHBOARD}
      onClick={onClick} onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}
    >
      <div className="sidebar-wagtail-branding__icon-wrapper">
        <img className="sidebar-wagtail-branding__icon" data-part="body" src={images.desktopLogoBody} alt="" />
        <img className="sidebar-wagtail-branding__icon" data-part="tail" src={images.desktopLogoTail} alt="" />
        <img className="sidebar-wagtail-branding__icon" data-part="eye--open" src={images.desktopLogoEyeOpen} alt="" />
        <img
          className="sidebar-wagtail-branding__icon" data-part="eye--closed" src={images.desktopLogoEyeClosed}
          alt=""
        />
      </div>
    </a>
  );
};

export class WagtailBrandingModuleDefinition implements ModuleDefinition {
  homeUrl: string;
  images: LogoImages;

  constructor(homeUrl: string, images: LogoImages) {
    this.homeUrl = homeUrl;
    this.images = images;
  }

  render({ strings, key, navigate }) {
    return (<WagtailBranding
      key={key} homeUrl={this.homeUrl} images={this.images}
      strings={strings} navigate={navigate}
    />);
  }
}
