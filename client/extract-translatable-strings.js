const { GettextExtractor, JsExtractors } = require('gettext-extractor');

const extractor = new GettextExtractor();

extractor
  .createJsParser([
    JsExtractors.callExpression('gettext', {
      arguments: {
        text: 0,
        context: 1,
      },
    }),
    JsExtractors.callExpression('gettext_noop', {
      arguments: {
        text: 0,
        context: 1,
      },
    }),
    JsExtractors.callExpression('ngettext', {
      arguments: {
        text: 1,
        textPlural: 2,
        context: 3,
      },
    }),
  ])
  .parseFilesGlob('./src/**/*.@(ts|js|tsx)');

extractor.savePotFile('../wagtail/admin/locale/en/LC_MESSAGES/djangojs.po');

extractor.printStats();
