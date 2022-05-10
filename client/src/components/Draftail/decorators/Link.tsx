import React from 'react';
import { ContentState, EditorState, Modifier, RichUtils } from 'draft-js';

import { gettext } from '../../../utils/gettext';
import Icon from '../../Icon/Icon';

import TooltipEntity from './TooltipEntity';

const LINK_ICON = <Icon name="link" />;
const BROKEN_LINK_ICON = <Icon name="warning" />;
const MAIL_ICON = <Icon name="mail" />;

const getEmailAddress = (mailto: string) =>
  mailto.replace('mailto:', '').split('?')[0];
const getPhoneNumber = (tel: string) => tel.replace('tel:', '').split('?')[0];
const getDomainName = (url: string) =>
  url.replace(/(^\w+:|^)\/\//, '').split('/')[0];

// Determines how to display the link based on its type: page, mail, anchor or external.
export const getLinkAttributes = (data: { url?: string; id?: string }) => {
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

interface LinkProps {
  entityKey: string;
  contentState: ContentState;
  children: React.ReactNode;
  onEdit: (entityKey: string) => void;
  onRemove: (entityKey: string) => void;
}

/**
 * Represents a link within the editor's content.
 */
const Link = (props: LinkProps): JSX.Element => {
  const { entityKey, contentState } = props;
  const data = contentState.getEntity(entityKey).getData();

  return <TooltipEntity {...props} {...getLinkAttributes(data)} />;
};

/**
 * See https://docs.djangoproject.com/en/4.0/_modules/django/core/validators/#EmailValidator.
 */
const djangoUserRegex =
  /(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$|^"([\001-\010\013\014\016-\037!#-[\]-\177]|\\[\001-\011\013\014\016-\177])*"$)/i;
const djangoDomainRegex =
  /((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))$/i;
/**
 * See https://docs.djangoproject.com/en/4.0/_modules/django/core/validators/#URLValidator.
 */
const djangoSchemes = ['http:', 'https:', 'ftp:', 'ftps:'];

export const getValidURL = (text: string) => {
  if (text.includes('@')) {
    const [user, domain] = text.split('@');
    if (djangoUserRegex.test(user) && djangoDomainRegex.test(domain)) {
      return `mailto:${text}`;
    }
  }

  try {
    const url = new URL(text);

    if (djangoSchemes.includes(url.protocol)) {
      return text;
    }
  } catch (e) {
    return false;
  }

  return false;
};

export const onPasteLink = (
  text: string,
  _: string | null,
  editorState: EditorState,
  { setEditorState }: { setEditorState: (state: EditorState) => void },
): 'handled' | 'not-handled' => {
  const url = getValidURL(text);

  if (!url) {
    return 'not-handled';
  }

  const selection = editorState.getSelection();
  let content = editorState.getCurrentContent();
  content = content.createEntity('LINK', 'MUTABLE', { url });
  const entityKey = content.getLastCreatedEntityKey();
  let nextState: EditorState;

  if (selection.isCollapsed()) {
    content = Modifier.insertText(
      content,
      selection,
      text,
      undefined,
      entityKey,
    );
    nextState = EditorState.push(editorState, content, 'insert-characters');
  } else {
    nextState = RichUtils.toggleLink(editorState, selection, entityKey);
  }

  setEditorState(nextState);
  return 'handled';
};

export default Link;
