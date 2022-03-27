// See https://stackoverflow.com/questions/44678315/how-to-import-markdown-md-file-in-typescript.
declare module '*.md';
declare module '*.html';

interface Window {
  WAGTAIL_ICONS: string[];
}
