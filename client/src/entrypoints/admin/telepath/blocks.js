import {
  FieldBlock,
  FieldBlockDefinition,
} from '../../../components/StreamField/blocks/FieldBlock';
import {
  ListBlock,
  ListBlockDefinition,
} from '../../../components/StreamField/blocks/ListBlock';
import {
  StaticBlock,
  StaticBlockDefinition,
} from '../../../components/StreamField/blocks/StaticBlock';
import {
  StreamBlock,
  StreamBlockDefinition,
} from '../../../components/StreamField/blocks/StreamBlock';
import {
  BlockGroupDefinition,
  StructBlock,
  StructBlockDefinition,
} from '../../../components/StreamField/blocks/StructBlock';

const wagtailStreamField = window.wagtailStreamField || {};

wagtailStreamField.blocks = {
  FieldBlock,
  FieldBlockDefinition,

  StaticBlock,
  StaticBlockDefinition,

  BlockGroupDefinition,
  StructBlock,
  StructBlockDefinition,

  ListBlock,
  ListBlockDefinition,

  StreamBlock,
  StreamBlockDefinition,
};

window.telepath.register('wagtail.blocks.FieldBlock', FieldBlockDefinition);
window.telepath.register('wagtail.blocks.StaticBlock', StaticBlockDefinition);
window.telepath.register('wagtail.blocks.BlockGroup', BlockGroupDefinition);
window.telepath.register('wagtail.blocks.StructBlock', StructBlockDefinition);
window.telepath.register('wagtail.blocks.ListBlock', ListBlockDefinition);
window.telepath.register('wagtail.blocks.StreamBlock', StreamBlockDefinition);

window.wagtailStreamField = wagtailStreamField;
