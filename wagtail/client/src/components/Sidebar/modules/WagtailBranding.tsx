import * as React from 'react';

import { gettext } from '../../../utils/gettext';
import { ModuleDefinition } from '../Sidebar';
import WagtailLogo from './WagtailLogo';

interface WagtailBrandingProps {
  homeUrl: string;
  slim: boolean;
  currentPath: string;
  navigate(url: string): void;
}

const WagtailBranding: React.FunctionComponent<WagtailBrandingProps> = ({
  homeUrl,
  slim,
  currentPath,
  navigate,
}) => {
  const brandingLogo = React.useMemo(
    () =>
      document.querySelector<HTMLTemplateElement>(
        '[data-wagtail-sidebar-branding-logo]',
      ),
    [],
  );
  const hasCustomBranding = brandingLogo && brandingLogo.innerHTML !== '';

  const onClick = (e: React.MouseEvent) => {
    // Do not capture click events with modifier keys or non-main buttons.
    if (e.ctrlKey || e.shiftKey || e.metaKey || (e.button && e.button !== 0)) {
      return;
    }

    e.preventDefault();
    navigate(homeUrl);
  };

  // Render differently if custom branding is provided.
  // This will only ever render once, so rendering before hooks is ok.
  if (hasCustomBranding) {
    return (
      <a
        className="sidebar-custom-branding"
        href={homeUrl}
        aria-label={gettext('Dashboard')}
        aria-current={currentPath === homeUrl ? 'page' : undefined}
        dangerouslySetInnerHTML={{
          __html: brandingLogo ? brandingLogo.innerHTML : '',
        }}
      />
    );
  }

  // Tail wagging
  // If the pointer changes direction 8 or more times without leaving, wag the tail!
  const lastMouseX = React.useRef(0);
  const lastDir = React.useRef<'r' | 'l'>('r');
  const dirChangeCount = React.useRef(0);
  const [isWagging, setIsWagging] = React.useState(false);

  const onMouseMove = (e: React.MouseEvent) => {
    const mouseX = e.pageX;
    const dir: 'r' | 'l' = mouseX > lastMouseX.current ? 'r' : 'l';

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

  const desktopClassName =
    'sidebar-wagtail-branding w-transition-all w-duration-150' +
    (isWagging ? ' sidebar-wagtail-branding--wagging' : '');

  return (
    <a
      className={desktopClassName}
      href={homeUrl}
      aria-label={gettext('Dashboard')}
      aria-current={currentPath === homeUrl ? 'page' : undefined}
      onClick={onClick}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
    >
      <div className="sidebar-wagtail-branding__icon-wrapper w-transition-all w-duration-150">
        <WagtailLogo slim={slim} />
      </div>
    </a>
  );
};

export class WagtailBrandingModuleDefinition implements ModuleDefinition {
  homeUrl: string;

  constructor(homeUrl: string) {
    this.homeUrl = homeUrl;
  }

  render({ slim, key, navigate, currentPath }) {
    return (
      <WagtailBranding
        key={key}
        homeUrl={this.homeUrl}
        slim={slim}
        navigate={navigate}
        currentPath={currentPath}
      />
    );
  }
}
