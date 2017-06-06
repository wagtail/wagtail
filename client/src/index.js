/**
 * Entry point for the wagtail package.
 * Re-exports components and other modules via a cleaner API.
 */

import Button from './components/Button/Button';
import Icon from './components/Icon/Icon';
import PublicationStatus from './components/PublicationStatus/PublicationStatus';
import LoadingSpinner from './components/LoadingSpinner/LoadingSpinner';
import Transition from './components/Transition/Transition';
import Explorer, {
  ExplorerToggle,
  initExplorer,
} from './components/Explorer';

export {
  Button,
  Icon,
  PublicationStatus,
  LoadingSpinner,
  Transition,
  Explorer,
  ExplorerToggle,
  initExplorer,
};
