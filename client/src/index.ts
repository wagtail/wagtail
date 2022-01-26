/**
 * Entry point for the wagtail package.
 * Re-exports components and other modules via a cleaner API.
 */

import Button from './components/Button/Button';
import Icon from './components/Icon/Icon';
import LoadingSpinner from './components/LoadingSpinner/LoadingSpinner';
import Portal from './components/Portal/Portal';
import PublicationStatus from './components/PublicationStatus/PublicationStatus';
import Transition from './components/Transition/Transition';
import { initFocusOutline } from './utils/focus';
import { initIE11Warning } from './includes/initIE11Warning';
import { initUpgradeNotification } from './components/UpgradeNotification';

export {
  Button,
  Icon,
  LoadingSpinner,
  Portal,
  PublicationStatus,
  Transition,
  initFocusOutline,
  initIE11Warning,
  initUpgradeNotification,
};
