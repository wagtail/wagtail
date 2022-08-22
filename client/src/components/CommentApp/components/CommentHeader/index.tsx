import React, { FunctionComponent, useState, useEffect, useRef } from 'react';

import { gettext } from '../../../../utils/gettext';
import Icon from '../../../Icon/Icon';
import type { Store } from '../../state';

import { Author } from '../../state/comments';

const dateOptions: Intl.DateTimeFormatOptions | any = {
  dateStyle: 'medium',
  timeStyle: 'short',
};
const dateTimeFormat = new Intl.DateTimeFormat([], dateOptions);

interface CommentReply {
  author: Author | null;
  date: number;
}

interface CommentHeaderProps {
  commentReply: CommentReply;
  store: Store;
  onResolve?(commentReply: CommentReply, store: Store): void;
  onEdit?(commentReply: CommentReply, store: Store): void;
  onDelete?(commentReply: CommentReply, store: Store): void;
  descriptionId?: string;
  focused: boolean;
}

export const CommentHeader: FunctionComponent<CommentHeaderProps> = ({
  commentReply,
  store,
  onResolve,
  onEdit,
  onDelete,
  descriptionId,
  focused,
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
    if (
      menuContainerRef.current &&
      e.target instanceof Node &&
      !menuContainerRef.current.contains(e.target)
    ) {
      setMenuOpen(false);
    }
  };

  useEffect(() => {
    document.addEventListener('click', handleClickOutside, true);
    return () => {
      document.removeEventListener('click', handleClickOutside, true);
    };
  }, []);

  const dateISO = new Date(date).toISOString();

  return (
    <div className="comment-header">
      <div className="comment-header__actions">
        {(onEdit || onDelete || onResolve) && (
          <div
            className="comment-header__action comment-header__action--more"
            ref={menuContainerRef}
          >
            <details open={menuOpen} onClick={toggleMenu}>
              <summary
                aria-label={gettext('More actions')}
                aria-haspopup="menu"
                role="button"
                onClick={toggleMenu}
                aria-expanded={menuOpen}
              >
                <Icon name="ellipsis-v" />
              </summary>

              <div
                className="comment-header__more-actions"
                role="menu"
                ref={menuRef}
              >
                {onEdit && (
                  <button type="button" role="menuitem" onClick={onClickEdit}>
                    {gettext('Edit')}
                  </button>
                )}
                {onDelete && (
                  <button type="button" role="menuitem" onClick={onClickDelete}>
                    {gettext('Delete')}
                  </button>
                )}
                {onResolve && (
                  <button
                    type="button"
                    role="menuitem"
                    onClick={onClickResolve}
                  >
                    {gettext('Resolve')}
                  </button>
                )}
              </div>
            </details>
          </div>
        )}
      </div>
      {author && author.avatarUrl && (
        <img className="comment-header__avatar" src={author.avatarUrl} alt="" />
      )}
      <span id={descriptionId}>
        <p className="comment-header__author">{author ? author.name : ''}</p>
        <p className="comment-header__date">
          <time dateTime={dateISO}>{dateTimeFormat.format(date)}</time>
        </p>
      </span>
    </div>
  );
};
