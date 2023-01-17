import { SnippetChooser } from '../../components/ChooserWidget/SnippetChooserWidget';

window.SnippetChooser = SnippetChooser;

function createSnippetChooser(id) {
  /* RemovedInWagtail50Warning */
  return new SnippetChooser(id);
}
window.createSnippetChooser = createSnippetChooser;
