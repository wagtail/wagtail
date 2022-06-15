/**
 * Entry point for the wagtail package.
 * Re-exports components and other modules via a cleaner API.
 */

export { default as Button } from './components/Button/Button';
export { default as Icon } from './components/Icon/Icon';
export { default as LoadingSpinner } from './components/LoadingSpinner/LoadingSpinner';
export { default as Portal } from './components/Portal/Portal';
export { default as PublicationStatus } from './components/PublicationStatus/PublicationStatus';
export { default as Transition } from './components/Transition/Transition';
export { default as initSkipLink } from './includes/initSkipLink';
export { initUpgradeNotification } from './includes/initUpgradeNotification';
