import PropTypes from 'prop-types';
import {
  Modifier,
  EditorState,
  RichUtils,
  convertFromHTML,
  ContentState,
  CharacterMetadata,
} from 'draft-js';
import React from 'react';

import { gettext } from '../../../utils/gettext';
import Icon from '../../Icon/Icon';

import TooltipEntity from './TooltipEntity';

const LINK_ICON = <Icon name="link" />;
const BROKEN_LINK_ICON = <Icon name="warning" />;
const MAIL_ICON = <Icon name="mail" />;

const getEmailAddress = (mailto) => mailto.replace('mailto:', '').split('?')[0];
const getPhoneNumber = (tel) => tel.replace('tel:', '').split('?')[0];
const getDomainName = (url) => url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

// Determines how to display the link based on its type: page, mail, anchor or external.
export const getLinkAttributes = (data) => {
  const url = data.url || null;
  let icon;
  let label;

  if (!url) {
    icon = BROKEN_LINK_ICON;
    label = gettext('Broken link');
  } else if (data.id) {
    icon = LINK_ICON;
    label = url;
  } else if (url.startsWith('mailto:')) {
    icon = MAIL_ICON;
    label = getEmailAddress(url);
  } else if (url.startsWith('tel:')) {
    icon = LINK_ICON;
    label = getPhoneNumber(url);
  } else if (url.startsWith('#')) {
    icon = LINK_ICON;
    label = url;
  } else {
    icon = LINK_ICON;
    label = getDomainName(url);
  }

  return {
    url,
    icon,
    label,
  };
};

/**
 * See https://docs.djangoproject.com/en/4.0/_modules/django/core/validators/#EmailValidator.
 */
// Compared to Django, changed to remove start and end of string checks.
const djangoUser =
  /([-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*|"([\001-\010\013\014\016-\037!#-[\]-\177]|\\[\001-\011\013\014\016-\177])*")/i;
// Compared to Django, changed to remove the end-of-domain `-` check that was done with a negative lookbehind `(?<!-)` (unsupported in Safari), and disallow all TLD hyphens instead.
// const djangoDomain = /((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))$/i;
const djangoDomain =
  /((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9]{2,63})/i;

const djangoEmail = new RegExp(
  `^${djangoUser.source}@${djangoDomain.source}$`,
  'i',
);

/**
 * See https://docs.djangoproject.com/en/4.0/_modules/django/core/validators/#URLValidator.
 */
const urlPattern = /(?:http|ftp)s?:\/\/[^\s]+/;

// Find URLs and email addresses within text, ready to use with RegExp g flag.
// Enforce URLs start at word boundaries, and end with whitespace.
// Essential so URLs can be auto-linked in a space-separated succession.
const linkPatternSource = `\\b(${urlPattern.source}|${djangoUser.source}@${djangoDomain.source})(\\s|$)`;

export const getValidLinkURL = (text) => {
  if (djangoEmail.test(text)) {
    return `mailto:${text}`;
  }

  // If there is whitespace, treat text as not a URL.
  // Prevents scenarios like `URL.parse('https://test.t/ http://a.b/')`.
  if (/\s/.test(text)) {
    return false;
  }

  try {
    // Switch to URL.canParse once we drop support for Safari 16.
    // eslint-disable-next-line no-new
    new URL(text);
  } catch (e) {
    return false;
  }

  if (urlPattern.test(text)) {
    return text;
  }

  return false;
};

const insertSingleLink = (editorState, text, url) => {
  const selection = editorState.getSelection();
  let content = editorState.getCurrentContent();
  content = content.createEntity('LINK', 'MUTABLE', { url });
  const entityKey = content.getLastCreatedEntityKey();

  if (selection.isCollapsed()) {
    content = Modifier.insertText(
      content,
      selection,
      text,
      undefined,
      entityKey,
    );
    return EditorState.push(editorState, content, 'insert-characters');
  }
  return RichUtils.toggleLink(editorState, selection, entityKey);
};

/**
 * Insert the pasted HTML or text, auto-linking URLs and emails.
 */
const insertContentWithLinks = (editorState, htmlOrText) => {
  const selection = editorState.getSelection();
  let content = editorState.getCurrentContent();

  const { contentBlocks, entityMap } = convertFromHTML(htmlOrText);
  const blockMap = ContentState.createFromBlockArray(
    contentBlocks,
    entityMap,
  ).getBlockMap();

  const blocks = blockMap.map((block) => {
    const blockText = block.getText();
    const pattern = new RegExp(linkPatternSource, 'ig');
    // Find matches in the block, confirm the URL, create the entity, store the range.
    const matches = Array.from(blockText.matchAll(pattern), (match) => {
      // Account for punctuation chars valid in URLs but unlikely to be intended.
      // For example "Go to https://example.com."
      // Terminal Punctuation class: see https://www.unicode.org/review/pr-23.html.
      const cleanURLPattern = match[1].replace(
        /\p{Terminal_Punctuation}+$/u,
        '',
      );
      const url = getValidLinkURL(cleanURLPattern);

      if (!url) return {};

      content = content.createEntity('LINK', 'MUTABLE', { url });

      return {
        start: match.index,
        end: match.index + cleanURLPattern.length,
        key: content.getLastCreatedEntityKey(),
      };
    });

    // Attach the link to the correct characters based on the matches’ ranges.
    const chars = block.getCharacterList().map((char, i) => {
      const match = matches.find(({ start, end }) => i >= start && i < end);
      if (match) {
        return CharacterMetadata.applyEntity(char, match.key);
      }
      return char;
    });

    return block.set('characterList', chars);
  });

  content = Modifier.replaceWithFragment(
    content,
    selection,
    blockMap.merge(blocks),
  );
  return EditorState.push(editorState, content, 'insert-characters');
};

export const onPasteLink = (text, html, editorState, { setEditorState }) => {
  const url = getValidLinkURL(text);

  if (url) {
    setEditorState(insertSingleLink(editorState, text, url));
    return 'handled';
  }

  if (new RegExp(linkPatternSource, 'gi').test(text)) {
    // Prefer the multi-line HTML clipboard data if present.
    setEditorState(insertContentWithLinks(editorState, html || text));
    return 'handled';
  }

  return 'not-handled';
};

/**
 * Represents a link within the editor's content.
 */
const Link = (props) => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();

  return <TooltipEntity {...props} {...getLinkAttributes(data)} />;
};

Link.propTypes = {
  entityKey: PropTypes.string.isRequired,
  contentState: PropTypes.object.isRequired,
};

export default Link;
