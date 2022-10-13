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
  const heading = panel?.querySelector<HTMLHeadingElement>(
    `#${panel?.getAttribute('aria-labelledby')}`,
  );
  const toggle = panel?.querySelector<HTMLButtonElement>('[data-panel-toggle]');
  const inlinePanelDeleted = anchor.closest(
    '[data-inline-panel-child].deleted',
  );
  if (!panel || !heading || !toggle || inlinePanelDeleted) {
    return null;
  }

  const label =
    heading.querySelector<HTMLSpanElement>('[data-panel-heading-text]')
      ?.textContent || heading.textContent?.replace(/\s+\*\s+$/g, '').trim();
  const isRequired =
    panel.querySelector<HTMLElement>('[data-panel-required]') !== null;
  const headingARIALevel = heading.getAttribute('aria-level');
  const headingLevel = headingARIALevel
    ? `h${headingARIALevel}`
    : heading.tagName.toLowerCase() || 'h2';
  const icon = toggle
    .querySelector<SVGUseElement>('use')
    ?.getAttribute('href')
    ?.replace('#icon-', '');
  return {
    anchor,
    toggle,
    icon: icon || '',
    label: label || '',
    href: anchor.getAttribute('href') || '',
    required: isRequired,
    errorCount: [].slice
      .call(panel.querySelectorAll('.error-message'))
      .filter((err) => err.closest('[data-panel]') === panel).length,
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
              // Use the target id when we observe sections rather than anchors.
              const href = target.getAttribute('href') || `#${target.id}` || '';
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
        // Count an element as "in", accounting for the 50px slim header and 70px actions footer.
        { root: null, rootMargin: '-50px 0px -70px 0px', threshold: 0.1 },
      );

    if (!observer) {
      setObserver(obs);
    } else {
      obs.disconnect();
    }

    links.forEach(({ anchor, href }, i) => {
      // Special-case for the "title" field, for which the anchor is hidden.
      const isFirst = i === 0;
      const isTitle = isFirst && href.includes('title');
      if (isTitle) {
        obs.observe(document.querySelector(href) as HTMLElement);
      } else {
        obs.observe(anchor);
      }
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

  const links = [].slice
    .call(
      anchorsContainer.querySelectorAll<HTMLAnchorElement>(
        '[data-panel-anchor]',
      ),
    )
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
