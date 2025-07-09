import {
  Widget,
  CheckboxInput,
  RadioSelect,
  Select,
} from '../../../components/Widget';

import {
  AdminDateInput,
  AdminTimeInput,
  AdminDateTimeInput,
} from '../../../components/DateTimeWidget';

window.telepath.register('wagtail.widgets.Widget', Widget);
window.telepath.register('wagtail.widgets.CheckboxInput', CheckboxInput);
window.telepath.register('wagtail.widgets.RadioSelect', RadioSelect);
window.telepath.register('wagtail.widgets.Select', Select);
window.telepath.register('wagtail.widgets.AdminDateInput', AdminDateInput);
window.telepath.register('wagtail.widgets.AdminTimeInput', AdminTimeInput);
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
