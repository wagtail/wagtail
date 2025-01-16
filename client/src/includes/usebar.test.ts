import { fireEvent } from '@testing-library/dom';

jest.useFakeTimers();

describe('handleTriggerKeyDown', () => {
  let trigger: HTMLElement;
  let showUserbar: jest.Mock;
  let setFocusToFirstItem: jest.Mock;
  let setFocusToLastItem: jest.Mock;

  beforeEach(() => {
    // Mocks
    showUserbar = jest.fn();
    setFocusToFirstItem = jest.fn();
    setFocusToLastItem = jest.fn();

    // Criação do elemento "trigger"
    trigger = document.createElement('button');
    trigger.setAttribute('aria-expanded', 'false');
    document.body.appendChild(trigger);

    // Mock do `document.activeElement`
    jest.spyOn(document, 'activeElement', 'get').mockImplementation(() => trigger);
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.restoreAllMocks();
    jest.clearAllTimers();
  });

  const handleTriggerKeyDown = (event: KeyboardEvent) => {
    if (
      trigger === document.activeElement &&
      trigger.getAttribute('aria-expanded') === 'false'
    ) {
      switch (event.key) {
        case 'ArrowUp':
          event.preventDefault();
          showUserbar(false);
          setTimeout(() => setFocusToLastItem(), 300);
          break;
        case 'ArrowDown':
          event.preventDefault();
          showUserbar(false);
          setTimeout(() => setFocusToFirstItem(), 300);
          break;
        default:
          break;
      }
    }
  };

  test('CT1: Trigger Focado e Fechado (ArrowUp)', () => {
    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    trigger.setAttribute('aria-expanded', 'false');
    fireEvent(trigger, event);

    handleTriggerKeyDown(event);

    expect(showUserbar).toHaveBeenCalledWith(false);
    jest.advanceTimersByTime(300);
    expect(setFocusToLastItem).toHaveBeenCalled();
  });

  test('CT2: Trigger Não Focado', () => {
    jest.spyOn(document, 'activeElement', 'get').mockImplementation(() => null);
    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    trigger.setAttribute('aria-expanded', 'false');
    fireEvent(trigger, event);

    handleTriggerKeyDown(event);

    expect(showUserbar).not.toHaveBeenCalled();
    expect(setFocusToLastItem).not.toHaveBeenCalled();
  });

  test('CT3: Trigger Focado e Aberto', () => {
    trigger.setAttribute('aria-expanded', 'true');
    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    fireEvent(trigger, event);

    handleTriggerKeyDown(event);

    expect(showUserbar).not.toHaveBeenCalled();
    expect(setFocusToLastItem).not.toHaveBeenCalled();
  });

  test('CT4: Userbar Fechada (ArrowDown)', () => {
    const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    trigger.setAttribute('aria-expanded', 'false');
    fireEvent(trigger, event);

    handleTriggerKeyDown(event);

    expect(showUserbar).toHaveBeenCalledWith(false);
    jest.advanceTimersByTime(300);
    expect(setFocusToFirstItem).toHaveBeenCalled();
  });

  test('CT5: Nenhuma Tecla Relevante', () => {
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    trigger.setAttribute('aria-expanded', 'false');
    fireEvent(trigger, event);

    handleTriggerKeyDown(event);

    expect(showUserbar).not.toHaveBeenCalled();
    expect(setFocusToFirstItem).not.toHaveBeenCalled();
    expect(setFocusToLastItem).not.toHaveBeenCalled();

    console.log(showUserbar.mock.calls);
    console.log(setFocusToLastItem.mock.calls);

  });
});

