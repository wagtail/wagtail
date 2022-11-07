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
        text: 0,
        textPlural: 1,
        context: 3,
      },
    }),
  ])
  .parseFilesGlob('./src/**/!(*.test).@(ts|js|tsx)');

extractor.savePotFile('../wagtail/admin/locale/en/LC_MESSAGES/djangojs.po');

extractor.printStats();
