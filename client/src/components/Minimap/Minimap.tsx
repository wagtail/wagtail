import React, { useEffect, useState, useRef } from 'react';

import { debounce } from '../../utils/debounce';
import { gettext } from '../../utils/gettext';
import Icon from '../Icon/Icon';

import CollapseAll from './CollapseAll';
import MinimapItem, { MinimapMenuItem } from './MinimapItem';

export interface MinimapProps {
  container: HTMLElement;
  anchorsContainer: HTMLElement;
  links: readonly MinimapMenuItem[];
  onUpdate: (container: HTMLElement) => void;
  toggleAllPanels: (expanded: boolean) => void;
}

const observerOptions = {
  root: null,
  // Count an element as "in", accounting for the 50px slim header and 70px actions footer.
  rootMargin: '-50px 0px -70px 0px',
  // 10% visibility within the boxed viewport is enough.
  threshold: 0.1,
};

type LinkIntersections = {
  [href: string]: boolean;
};

const mapIntersections = (
  acc: LinkIntersections,
  { target, isIntersecting }: IntersectionObserverEntry,
) => {
  const href = `#${target.closest('[data-panel]')?.id}` || '';
  acc[href] = isIntersecting;
  return acc;
};

/**
 * For cases where the minimap has more item than can fit in the viewport,
 * we need to keep its scroll position updated to follow page scrolling.
 */
const updateScrollPosition = (list: HTMLOListElement) => {
  const activeLinks = list.querySelectorAll<HTMLElement>(
    'a[aria-current="true"]',
  );

  if (activeLinks.length === 0) {
    return;
  }

  const firstActive = activeLinks[0];
  const lastActive = activeLinks[activeLinks.length - 1];
  let newScroll = list.scrollTop;
  if (firstActive) {
    if (firstActive.offsetTop < list.scrollTop) {
      newScroll = firstActive.offsetTop;
    }
  }
  if (lastActive) {
    if (lastActive.offsetTop > list.scrollTop + list.offsetHeight) {
      newScroll =
        lastActive.offsetTop - list.offsetHeight + lastActive.offsetHeight;
    }
  }

  // Scroll changes require mutating this property.
  // eslint-disable-next-line no-param-reassign
  list.scrollTop = newScroll;
};

/**
 * Minimap sidebar menu, with one internal link per section of the page.
 * The minimap has a lot of advanced behavior:
 * - It opens and closes based on hover, except if interacted with.
 * - It also opens and closes when clicking its toggle.
 * - It closes when clicking outside.
 * - It uses IntersectionObserver to display which menu items are currently "visible" on the page.
 */
const Minimap: React.FunctionComponent<MinimapProps> = ({
  container,
  anchorsContainer,
  links,
  onUpdate,
  toggleAllPanels,
}) => {
  const [expanded, setExpanded] = useState<boolean>(false);
  // Keep track of whether we should keep the minimap expanded (should auto-close on mouseout if not interacted with).
  const [keepExpanded, setKeepExpanded] = useState<boolean>(false);
  // Collapse all yes/no state.
  const [panelsExpanded, setPanelsExpanded] = useState<boolean>(true);
  const [intersections, setIntersections] = useState<LinkIntersections>({});
  const observer = useRef<IntersectionObserver | null>(null);
  const lastIntersections = useRef({});
  const updateLinks = useRef<CallableFunction | null>(null);
  const listRef = useRef<HTMLOListElement>(null);

  // Keep track of all the different ways the minimap can be opened and closed.
  const onMouseOver = () => {
    if (window.matchMedia('(hover: hover)').matches) {
      // Opening with hover should not keep the menu expanded.
      setExpanded(true);
    }
  };
  const onMouseOut = () => {
    if (window.matchMedia('(hover: hover)').matches) {
      if (!keepExpanded) {
        setExpanded(false);
        setKeepExpanded(false);
      }
    }
  };
  const onClickToggle = () => {
    setExpanded(!expanded);
    setKeepExpanded(!expanded);
  };
  const onClickLink = (e: React.MouseEvent) => {
    // Prevent navigating if the link is only partially shown.
    if (!expanded) {
      e.preventDefault();
    }
    setExpanded(true);
    setKeepExpanded(true);
  };

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (container.contains(e.target as HTMLElement)) {
        return;
      }
      setExpanded(false);
      setKeepExpanded(false);
    };
    document.addEventListener('click', onClickOutside, true);
  }, []);

  /**
   * Performance-sensitive intersections calculations with a double debounce:
   * - With the IntersectionObserver API, the browser decides how often to update us, compared to constant `scroll`.
   * - We keep track of intersecting elements on every IntersectionObserver update,
   * - but only update the links after updates have stopped for 100ms.
   */
  useEffect(() => {
    const obsCallback = (newEntries) => {
      lastIntersections.current = newEntries.reduce(mapIntersections, {
        ...lastIntersections.current,
      });

      if (!updateLinks.current) {
        updateLinks.current = debounce((newIntersections) => {
          setIntersections(newIntersections);
          updateScrollPosition(listRef.current as HTMLOListElement);
        }, 100);
      }

      updateLinks.current(lastIntersections.current);

      // Support for InlinePanel removals: when they stop intersecting, re-render the whole minimap.
      newEntries.forEach(({ target }) => {
        const deletedInlinePanel = target.closest('.deleted');
        if (deletedInlinePanel) {
          onUpdate(container);
        }
      });
    };

    if (!observer.current) {
      observer.current = new IntersectionObserver(obsCallback, observerOptions);
    }

    const obs = observer.current as IntersectionObserver;

    obs.disconnect();

    links.forEach(({ panel, toggle }) => {
      // Special-case for top-level InlinePanel and StreamField, where the
      // link only shows as active if the anchor is in view.
      const isTopLevelNested =
        panel.matches('.w-panel--nested') &&
        panel.closest('[data-field]') === null;
      obs.observe(isTopLevelNested ? toggle : panel);
    });

    return () => {
      obs.disconnect();
    };
  }, [links, container]);

  useEffect(() => {
    // Reset the "collapse all" when switching tabs.
    setPanelsExpanded(true);
  }, [anchorsContainer, setPanelsExpanded]);

  return (
    <div>
      <CollapseAll
        expanded={panelsExpanded}
        onClick={() => {
          setPanelsExpanded(!panelsExpanded);
          toggleAllPanels(!panelsExpanded);
        }}
        floating
        insideMinimap={expanded}
      />
      {/* Keyboard support is implemented with the toggle button. */}
      {/* eslint-disable-next-line jsx-a11y/mouse-events-have-key-events */}
      <div
        className={`w-minimap ${expanded ? 'w-minimap--expanded' : ''}`}
        onMouseOver={onMouseOver}
        onMouseOut={onMouseOut}
      >
        <div className="w-minimap__header">
          <button
            type="button"
            aria-expanded={expanded}
            onClick={onClickToggle}
            className="w-minimap__toggle"
            // Not the most correct label, but matches side panels with similar toggles.
            aria-label={gettext('Toggle side panel')}
          >
            <Icon name="expand-right" />
          </button>
        </div>
        <ol className="w-minimap__list" ref={listRef}>
          {links.map((link) => (
            <li key={link.href}>
              <MinimapItem
                item={link}
                intersects={intersections[link.href]}
                expanded={expanded}
                onClick={onClickLink}
              />
            </li>
          ))}
        </ol>
        <div className="w-minimap__footer" />
      </div>
    </div>
  );
};

export default Minimap;
