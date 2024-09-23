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

window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);
window.telepath.register('wagtail.blocks.StaticBlock', StaticBlockDefinition);
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);

window.wagtailStreamField = wagtailStreamField;
