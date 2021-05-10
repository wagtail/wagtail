import {
  Button,
  Icon,
  PublicationStatus,
  LoadingSpinner,
  Portal,
  Transition,
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

  it('has Portal', () => {
    expect(Portal).toBeDefined();
  });

  it('has Transition', () => {
    expect(Transition).toBeDefined();
  });
});
