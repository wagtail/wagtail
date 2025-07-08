import {
  Widget,
  CheckboxInput,
  RadioSelect,
  Select,
} from '../../../components/Widget';

window.telepath.register('wagtail.widgets.Widget', Widget);
window.telepath.register('wagtail.widgets.CheckboxInput', CheckboxInput);
window.telepath.register('wagtail.widgets.RadioSelect', RadioSelect);
window.telepath.register('wagtail.widgets.Select', Select);

class BaseDateTimeWidget extends Widget {
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

class AdminDateInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateChooser;
}
window.telepath.register('wagtail.widgets.AdminDateInput', AdminDateInput);

class AdminTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initTimeChooser;
}
window.telepath.register('wagtail.widgets.AdminTimeInput', AdminTimeInput);

class AdminDateTimeInput extends BaseDateTimeWidget {
  initChooserFn = window.initDateTimeChooser;
}
window.telepath.register(
  'wagtail.widgets.AdminDateTimeInput',
  AdminDateTimeInput,
);

class ValidationError {
  constructor(messages) {
    this.messages = messages;
  }
}
window.telepath.register('wagtail.errors.ValidationError', ValidationError);
