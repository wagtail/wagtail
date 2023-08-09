import PropTypes from 'prop-types';
import { Modifier, EditorState, RichUtils } from 'draft-js';
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
const djangoUserRegex =
  /(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*$|^"([\001-\010\013\014\016-\037!#-[\]-\177]|\\[\001-\011\013\014\016-\177])*"$)/i;
// Compared to Django, changed to remove the end-of-domain `-` check that was done with a negative lookbehind `(?<!-)` (unsupported in Safari), and disallow all TLD hyphens instead.
// const djangoDomainRegex = /((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9-]{2,63}(?<!-))$/i;
const djangoDomainRegex =
  /((?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+)(?:[A-Z0-9]{2,63})$/i;
/**
 * See https://docs.djangoproject.com/en/4.0/_modules/django/core/validators/#URLValidator.
 */
const djangoSchemes = ['http:', 'https:', 'ftp:', 'ftps:'];

export const getValidLinkURL = (text, schemes) => {
  if (text.includes('@')) {
    const [user, domain] = text.split('@');
    if (djangoUserRegex.test(user) && djangoDomainRegex.test(domain)) {
      return `mailto:${text}`;
    }
  }

  try {
    const url = new URL(text);

    if (schemes.includes(url.protocol)) {
      return text;
    }
  } catch (e) {
    return false;
  }

  return false;
};

export const onPasteLink = (text, html, editorState, { setEditorState }) => {
  const url = getValidLinkURL(text, djangoSchemes);

  if (!url) {
    return 'not-handled';
  }

  const selection = editorState.getSelection();
  let content = editorState.getCurrentContent();
  content = content.createEntity('LINK', 'MUTABLE', { url });
  const entityKey = content.getLastCreatedEntityKey();
  let nextState;

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
