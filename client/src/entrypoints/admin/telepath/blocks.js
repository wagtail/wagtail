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
} from '../../../components/StreamField/blocks/StructBlock';
import {
  ListBlock,
  ListBlockDefinition,
} from '../../../components/StreamField/blocks/ListBlock';
import {
  StreamBlock,
  StreamBlockDefinition,
} from '../../../components/StreamField/blocks/StreamBlock';

const wagtailStreamField = window.wagtailStreamField || {};

wagtailStreamField.blocks = {
  FieldBlock,
  FieldBlockDefinition,

  StaticBlock,
  StaticBlockDefinition,

  StructBlock,
  StructBlockDefinition,

  ListBlock,
  ListBlockDefinition,

  StreamBlock,
  StreamBlockDefinition,
};

function initBlockWidget(id) {
  /*
  Initialises the top-level element of a BlockWidget
  (the form widget for a StreamField).
  Receives the ID of a DOM element with the attributes:
    data-block: JSON-encoded block definition to be passed to telepath.unpack
      to obtain a Javascript representation of the block
      (an instance of one of the Block classes below)
    data-value: JSON-encoded value for this block
  */

  const body = document.querySelector('#' + id + '[data-block]');

  // unpack the block definition and value
  const blockDefData = JSON.parse(body.dataset.block);
  const blockDef = window.telepath.unpack(blockDefData);
  const blockValue = JSON.parse(body.dataset.value);
  const blockError = JSON.parse(body.dataset.error);

  // replace the 'body' element with the populated HTML structure for the block
  blockDef.render(body, id, blockValue, blockError);
}
window.initBlockWidget = initBlockWidget;

window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);
window.telepath.register('wagtail.blocks.StaticBlock', StaticBlockDefinition);
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);

window.wagtailStreamField = wagtailStreamField;
