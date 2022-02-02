import {
  FieldBlock,
  FieldBlockDefinition,
} from '../../../components/StreamField/blocks/FieldBlock';
import {
  StaticBlock,
  StaticBlockDefinition,
} from '../../../components/StreamField/blocks/StaticBlock';
import {
  StructBlock,
  StructBlockDefinition,
  StructBlockValidationError,
} from '../../../components/StreamField/blocks/StructBlock';
import {
  ListBlock,
  ListBlockDefinition,
  ListBlockValidationError,
} from '../../../components/StreamField/blocks/ListBlock';
import {
  StreamBlock,
  StreamBlockDefinition,
  StreamBlockValidationError,
} from '../../../components/StreamField/blocks/StreamBlock';

const wagtailStreamField = window.wagtailStreamField || {};

wagtailStreamField.blocks = {
  FieldBlock,
  FieldBlockDefinition,

  StaticBlock,
  StaticBlockDefinition,

  StructBlock,
  StructBlockDefinition,
  StructBlockValidationError,

  ListBlock,
  ListBlockDefinition,
  ListBlockValidationError,

  StreamBlock,
  StreamBlockDefinition,
  StreamBlockValidationError,
};

function initBlockWidget(id) {
  /*
  Initialises the top-level element of a BlockWidget
  (i.e. the form widget for a StreamField).
  Receives the ID of a DOM element with the attributes:
    data-block: JSON-encoded block definition to be passed to telepath.unpack
      to obtain a Javascript representation of the block
      (i.e. an instance of one of the Block classes below)
    data-value: JSON-encoded value for this block
  */

  const body = document.querySelector('#' + id + '[data-block]');

  // unpack the block definition and value
  const blockDefData = JSON.parse(body.dataset.block);
  const blockDef = window.telepath.unpack(blockDefData);
  const blockValue = JSON.parse(body.dataset.value);
  const blockErrors = window.telepath.unpack(JSON.parse(body.dataset.errors));

  // replace the 'body' element with the populated HTML structure for the block
  blockDef.render(body, id, blockValue, blockErrors);
}
window.initBlockWidget = initBlockWidget;

window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);
window.telepath.register('wagtail.blocks.StaticBlock', StaticBlockDefinition);
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);
window.telepath.register(
  'wagtail.blocks.StructBlockValidationError',
  StructBlockValidationError,
);
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);
window.telepath.register(
  'wagtail.blocks.ListBlockValidationError',
  ListBlockValidationError,
);
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);
window.telepath.register(
  'wagtail.blocks.StreamBlockValidationError',
  StreamBlockValidationError,
);

window.wagtailStreamField = wagtailStreamField;
