/**
 * Widget classes for date and time inputs. These depend on window.initDateChooser,
 * window.initTimeChooser, and window.initDateTimeChooser being defined, which is done
 * by entrypoints/admin/date-time-chooser.js.
 */

import { Widget } from '../Widget';

export class BaseDateTimeWidget extends Widget {
  constructor(options) {
    super();
    this.options = options;
  }

  render(placeholder, name, id, initialState) {
    const element = document.createElement('input');
    element.type = 'text';
    element.name = name;
    element.id = id;
    placeholder.replaceWith(element);

    this.initChooserFn(id, this.options);

    const widget = {
      getValue() {
        return element.value;
      },
      getState() {
        return element.value;
      },
      setState(state) {
        element.value = state;
      },
      setInvalid(invalid) {
        if (invalid) {
          element.setAttribute('aria-invalid', 'true');
        } else {
          element.removeAttribute('aria-invalid');
        }
      },
      focus(opts) {
        // focusing opens the date picker, so don't do this if it's a 'soft' focus
        if (opts && opts.soft) return;
        element.focus();
      },
      getTextLabel() {
        return this.getValue() || '';
      },
      idForLabel: id,
    };
    widget.setState(initialState);
    return widget;
  }
}

export class AdminDateInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateChooser;
}

export class AdminTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initTimeChooser;
}

export class AdminDateTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateTimeChooser;
}
