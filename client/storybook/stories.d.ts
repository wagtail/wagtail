// See https://stackoverflow.com/questions/44678315/how-to-import-markdown-md-file-in-typescript.
declare module '*.md';
declare module '*.html';

interface Window {
  PATTERN_LIBRARY_API: string;
}
