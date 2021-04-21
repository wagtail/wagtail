/* eslint-disable react/prop-types */

import dateFormat from 'dateformat';
import React, { FunctionComponent } from 'react';
import Icon from '../../../Icon/Icon';
import type { Store } from '../../state';
import { TranslatableStrings } from '../../main';

import { Author } from '../../state/comments';


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
}

export const CommentHeader: FunctionComponent<CommentHeaderProps> = ({
  commentReply, store, strings, onResolve, onEdit, onDelete, descriptionId
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

  return (
    <div className="comment-header">
      <div className="comment-header__actions">
        {onResolve &&
          <div className="comment-header__action comment-header__action--resolve">
            <button type="button" aria-label={strings.RESOLVE} onClick={onClickResolve}>
              <Icon name="check" />
            </button>
          </div>
        }
        {(onEdit || onDelete) &&
          <div className="comment-header__action comment-header__action--more">
            <details>
              <summary aria-label={strings.MORE_ACTIONS} aria-haspopup="menu" role="button">
                <Icon name="ellipsis-v" />
              </summary>

              <div className="comment-header__more-actions" role="menu">
                {onEdit && <button type="button" role="menuitem" onClick={onClickEdit}>{strings.EDIT}</button>}
                {onDelete && <button type="button" role="menuitem" onClick={onClickDelete}>{strings.DELETE}</button>}
              </div>
            </details>
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
