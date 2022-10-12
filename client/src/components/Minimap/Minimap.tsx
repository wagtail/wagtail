import React, { useEffect, useState, useRef } from 'react';
import ReactDOM from 'react-dom';

import { debounce } from '../../utils/debounce';
import Icon from '../Icon/Icon';

import MinimapItem, { MinimapMenuItem } from './MinimapItem';

export interface MinimapProps {
  container: HTMLElement;
  anchorsContainer: HTMLElement;
  links: readonly MinimapMenuItem[];
  onUpdate: () => void;
}

const createMinimapLink = (
  anchor: HTMLAnchorElement,
): MinimapMenuItem | null => {
  const panel = anchor.closest<HTMLElement>('[data-panel]');
  const inlinePanelDeleted = anchor.closest(
    '[data-inline-panel-child].deleted',
  );
  if (!panel || inlinePanelDeleted) {
    return null;
  }

  const heading = panel.querySelector<HTMLHeadingElement>(
    `#${panel.getAttribute('aria-labelledby')}`,
  );
  const label = heading?.querySelector<HTMLSpanElement>(
    '[data-panel-heading-text]',
  )?.textContent;
  const isRequired =
    panel.querySelector<HTMLElement>('[data-panel-required]') !== null;
  const headingARIALevel = heading?.getAttribute('aria-level');
  const headingLevel = headingARIALevel
    ? `h${headingARIALevel}`
    : heading?.tagName.toLowerCase() || 'h2';
  return {
    anchor,
    icon: 'minus',
    label: label || '',
    href: anchor.getAttribute('href') || '',
    required: isRequired,
    errorCount: panel.querySelectorAll('.error-message').length,
    level: headingLevel as MinimapMenuItem['level'],
  };
};

/**
 * TODO;
 */
const Minimap: React.FunctionComponent<MinimapProps> = ({
  container,
  anchorsContainer,
  links,
  onUpdate,
}) => {
  const [observer, setObserver] = useState<IntersectionObserver | null>(null);
  const [expanded, setExpanded] = useState<boolean>(false);
  const [intersections, setIntersections] = useState<{
    [href: string]: boolean;
  }>({});
  const intersectionsRef = useRef(intersections);
  const updateMinimap = useRef<CallableFunction | null>(null);

  useEffect(() => {
    const obs =
      observer ||
      new IntersectionObserver(
        (newEntries) => {
          intersectionsRef.current = newEntries.reduce(
            (acc, { target, isIntersecting }: IntersectionObserverEntry) => {
              const href = target.getAttribute('href') || '';
              acc[href] = isIntersecting;
              return acc;
            },
            { ...intersectionsRef.current },
          );

          if (!updateMinimap.current) {
            updateMinimap.current = debounce((latestIntersections) => {
              setIntersections(latestIntersections);

              const latestAnchorsCount = anchorsContainer.querySelectorAll(
                '[data-panel-anchor]',
              ).length;
              if (latestAnchorsCount !== links.length) {
                onUpdate();
              }
            }, 300);
          }

          updateMinimap.current(intersectionsRef.current);

          newEntries.forEach(({ target }) => {
            if (!document.body.contains(target) || target.closest('.deleted')) {
              onUpdate();
            }
          });
        },
        { root: null, rootMargin: '0px', threshold: 0.1 },
      );

    if (!observer) {
      setObserver(obs);
    } else {
      obs.disconnect();
    }

    links.forEach(({ anchor }) => {
      obs.observe(anchor);
    });

    return () => {
      obs.disconnect();
    };
  }, [observer, links, setIntersections]);

  useEffect(() => {
    document.addEventListener(
      'click',
      (e: MouseEvent) => {
        if (!container.contains(e.target as HTMLElement)) {
          setExpanded(false);
        }
      },
      true,
    );
  }, [container, expanded]);

  return (
    <div className={`w-minimap${expanded ? ' w-minimap--expanded' : ''}`}>
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => setExpanded(false)}
        className="w-minimap__toggle"
      >
        {expanded ? <Icon name="expand-right" /> : <Icon name="minus" />}
      </button>
      <ol className="w-minimap__list">
        {links.map((link) => (
          <li key={link.href}>
            <MinimapItem
              item={link}
              intersects={intersections[link.href]}
              onClick={() => setExpanded(true)}
            />
          </li>
        ))}
      </ol>
    </div>
  );
};

const renderMinimap = (container: HTMLElement) => {
  const tabs = document.querySelector('[data-tabs]');
  let anchorsContainer: HTMLElement = document.body;

  if (tabs) {
    const activeTab = tabs.querySelector('[role="tab"][aria-selected="true"]');
    const activeTabpanel = tabs.querySelector<HTMLDivElement>(
      `#${activeTab?.getAttribute('aria-controls')}`,
    );
    anchorsContainer = activeTabpanel || anchorsContainer;
  }

  const links = [
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    ...anchorsContainer.querySelectorAll<HTMLAnchorElement>(
      '[data-panel-anchor]',
    ),
  ]
    .map(createMinimapLink)
    .filter(Boolean);

  ReactDOM.render(
    <Minimap
      container={container}
      anchorsContainer={anchorsContainer}
      links={links as MinimapMenuItem[]}
      onUpdate={renderMinimap.bind(null, container)}
    />,
    container,
  );
};

export const initMinimap = (
  container = document.querySelector<HTMLDivElement>(
    '[data-minimap-container]',
  ),
) => {
  if (!container) {
    return;
  }

  const updateMinimap = debounce(renderMinimap.bind(null, container), 300);
  const tabs = document.querySelector('[data-tabs]');

  if (tabs) {
    document.addEventListener('wagtail:tab-changed', updateMinimap);
  }

  document.addEventListener('wagtail:panel-init', updateMinimap);

  container.style.setProperty('--offset-top', `${container.offsetTop}px`);

  renderMinimap(container);
};

export default Minimap;
