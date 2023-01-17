import { PageChooser } from '../../components/ChooserWidget/PageChooserWidget';

window.PageChooser = PageChooser;

function createPageChooser(id, parentId, options) {
  /* RemovedInWagtail50Warning */
  return new PageChooser(id, parentId, options);
}
window.createPageChooser = createPageChooser;
