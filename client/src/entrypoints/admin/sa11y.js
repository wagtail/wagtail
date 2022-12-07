import { Sa11y, Lang, LangEn, Sa11yCustomChecks } from 'sa11y';

Lang.addI18n(LangEn.strings);
const sa11y = new Sa11y({
  customChecks: new Sa11yCustomChecks(),
  checkRoot: 'body',
  readabilityRoot: 'main',
});
