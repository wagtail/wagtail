/* eslint-disable react/prop-types */

import React from 'react';
import { ModuleDefinition } from '../Sidebar';

export interface LogoImages {
    mobileLogo: string;
    desktopLogoBody: string
    desktopLogoTail: string;
    desktopLogoEyeOpen: string;
    desktopLogoEyeClosed: string;
}

interface WagtailBrandingProps {
    collapsed: boolean;
    images: LogoImages;
    homeUrl: string;
    navigate(url: string): void;
}

const WagtailBranding: React.FunctionComponent<WagtailBrandingProps> = ({ images, homeUrl, navigate }) => {
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

  return (
    <a className="sidebar-wagtail-branding" href="#" onClick={onClick} aria-label={'Dashboard'}>{/* GETTEXT */}
      <div className={'sidebar-wagtail-branding__desktop' + (isWagging ? ' sidebar-wagtail-branding__desktop--wagging' : '')} onMouseMove={onMouseMove} onMouseLeave={onMouseLeave}>
        <div>
          <img data-part="body" src={images.desktopLogoBody} alt="" />
          <img data-part="tail" src={images.desktopLogoTail} alt="" />
          <img data-part="eye--open" src={images.desktopLogoEyeOpen} alt="" />
          <img data-part="eye--closed" src={images.desktopLogoEyeClosed} alt="" />
        </div>
      </div>
      {/* TODO Do we need this? <span className="u-hidden@sm">{'Dashboard'}</span> */}{/* GETTEXT */}
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

    render({ collapsed, navigate }) {
      return <WagtailBranding homeUrl={this.homeUrl} images={this.images} collapsed={collapsed} navigate={navigate} />;
    }
}
