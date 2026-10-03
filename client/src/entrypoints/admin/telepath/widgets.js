import {
  BlockWidget,
  CheckboxInput,
  RadioSelect,
  Select,
  Widget,
} from '../../../components/Widget';

window.telepath.register('wagtail.widgets.Widget', Widget);
window.telepath.register('wagtail.widgets.CheckboxInput', CheckboxInput);
window.telepath.register('wagtail.widgets.RadioSelect', RadioSelect);
window.telepath.register('wagtail.widgets.Select', Select);
window.telepath.register('wagtail.widgets.BlockWidget', BlockWidget);

class ValidationError {
  constructor(messages) {
    this.messages = messages;
  }
}
window.telepath.register('wagtail.errors.ValidationError', ValidationError);
