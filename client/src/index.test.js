import {
  Button,
  Icon,
  PublicationStatus,
  LoadingSpinner,
  Transition,
  Explorer,
  ExplorerToggle,
  initExplorer,
} from './index';

describe('wagtail package API', () => {
  it('has Button', () => {
    expect(Button).toBeDefined();
  });

  it('has Icon', () => {
    expect(Icon).toBeDefined();
  });

  it('has PublicationStatus', () => {
    expect(PublicationStatus).toBeDefined();
  });

  it('has LoadingSpinner', () => {
    expect(LoadingSpinner).toBeDefined();
  });

  it('has Transition', () => {
    expect(Transition).toBeDefined();
  });

  it('has Explorer', () => {
    expect(Explorer).toBeDefined();
  });

  it('has ExplorerToggle', () => {
    expect(ExplorerToggle).toBeDefined();
  });

  it('has initExplorer', () => {
    expect(initExplorer).toBeDefined();
  });
});
