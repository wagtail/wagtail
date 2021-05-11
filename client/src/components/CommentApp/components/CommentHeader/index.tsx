/* eslint-disable react/prop-types */

import dateFormat from 'dateformat';
import React, { FunctionComponent, useState, useEffect, useRef } from 'react';
import Icon from '../../../Icon/Icon';
import type { Store } from '../../state';
import { TranslatableStrings } from '../../main';
import { IS_IE11 } from '../../../../config/wagtailConfig';

import { Author } from '../../state/comments';

// Details/Summary components that just become <details>/<summary> tags
// except for IE11 where they become <div> tags to allow us to style them
const Details: React.FunctionComponent<React.ComponentPropsWithoutRef<'details'>> = (
  ({ children, open, ...extraProps }) => {
    if (IS_IE11) {
      return (
        <div className={'details-fallback' + (open ? ' details-fallback--open' : '')} {...extraProps}>
          {children}
        </div>
      );
    }

    return (
      <details open={open} {...extraProps}>
        {children}
      </details>
    );
  }
);

const Summary: React.FunctionComponent<React.ComponentPropsWithoutRef<'summary'>> = ({ children, ...extraProps }) => {
  if (IS_IE11) {
    return (
      <button
        className="details-fallback__summary"
        {...extraProps}
      >
        {children}
      </button>
    );
  }

  return (
    <summary {...extraProps}>
      {children}
    </summary>
  );
};

interface CommentReply {
  author: Author | null;
  date: number;
}

interface CommentHeaderProps {
  commentReply: CommentReply;
  store: Store;
  strings: TranslatableStrings;
  onResolve?(commentReply: CommentReply, store: Store): void;
  onEdit?(commentReply: CommentReply, store: Store): void;
  onDelete?(commentReply: CommentReply, store: Store): void;
  descriptionId?: string;
  focused: boolean;
}

export const CommentHeader: FunctionComponent<CommentHeaderProps> = ({
  commentReply, store, strings, onResolve, onEdit, onDelete, descriptionId, focused
}) => {
  const { author, date } = commentReply;

  const onClickResolve = (e: React.MouseEvent) => {
    e.preventDefault();

    if (onResolve) {
      onResolve(commentReply, store);
    }
  };

  const onClickEdit = async (e: React.MouseEvent) => {
    e.preventDefault();

    if (onEdit) {
      onEdit(commentReply, store);
    }
  };

  const onClickDelete = async (e: React.MouseEvent) => {
    e.preventDefault();

    if (onDelete) {
      onDelete(commentReply, store);
    }
  };

  const [menuOpen, setMenuOpen] = useState(false);
  useEffect(() => {
    if (menuOpen && !focused) {
      setMenuOpen(false);
    }
  }, [focused]);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuContainerRef = useRef<HTMLDivElement>(null);

  const toggleMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setMenuOpen(!menuOpen);
  };

  useEffect(() => {
    if (menuOpen) {
      setTimeout(() => menuRef.current?.focus(), 1);
    }
  }, [menuOpen]);

  const handleClickOutside = (e: MouseEvent) => {
    if (menuContainerRef.current && e.target instanceof Node && !menuContainerRef.current.contains(e.target)) {
      setMenuOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  return (
    <div className="comment-header">
      <div className="comment-header__actions">
        {(onEdit || onDelete || onResolve) &&
          <div className="comment-header__action comment-header__action--more" ref={menuContainerRef}>
            <Details open={menuOpen} onClick={toggleMenu}>
              <Summary
                aria-label={strings.MORE_ACTIONS}
                aria-haspopup="menu"
                role="button"
                onClick={toggleMenu}
                aria-expanded={menuOpen}
              >
                <Icon name="ellipsis-v" />
              </Summary>

              <div className="comment-header__more-actions" role="menu" ref={menuRef}>
                {onEdit && <button type="button" role="menuitem" onClick={onClickEdit}>{strings.EDIT}</button>}
                {onDelete && <button type="button" role="menuitem" onClick={onClickDelete}>{strings.DELETE}</button>}
                {onResolve && <button type="button" role="menuitem" onClick={onClickResolve}>{strings.RESOLVE}</button>}
              </div>
            </Details>
          </div>
        }
      </div>
      {author && author.avatarUrl &&
        <img className="comment-header__avatar" src={author.avatarUrl} role="presentation" />}
      <span id={descriptionId}>
        <p className="comment-header__author">{author ? author.name : ''}</p>
        <p className="comment-header__date">{dateFormat(date, 'd mmm yyyy HH:MM')}</p>
      </span>
    </div>
  );
};
