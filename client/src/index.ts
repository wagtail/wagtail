/**
 * Entry point for the wagtail package.
 * Re-exports components and other modules via a cleaner API.
 */

export { default as Button } from './sidebar/components/Button/Button';
export { default as Icon } from './components/Icon/Icon';
export { default as LoadingSpinner } from './sidebar/components/LoadingSpinner/LoadingSpinner';
export { default as Portal } from './components/Portal/Portal';
export { default as PublicationStatus } from './sidebar/components/PublicationStatus/PublicationStatus';
export { default as Transition } from './sidebar/components/Transition/Transition';
export { initUpgradeNotification } from './components/UpgradeNotification';
export { initSkipLink } from './includes/initSkipLink';
