import React from 'react';

import { gettext } from '../../../../utils/gettext';
import type { Store } from '../../state';
import type { Comment, CommentReply, Author } from '../../state/comments';
import { updateReply, deleteReply } from '../../actions/comments';
import { CommentHeader } from '../CommentHeader';
import TextArea from '../TextArea';
import Icon from '../../../Icon/Icon';

export async function saveCommentReply(
  comment: Comment,
  reply: CommentReply,
  store: Store,
) {
  store.dispatch(
    updateReply(comment.localId, reply.localId, {
      mode: 'saving',
    }),
  );

  try {
    store.dispatch(
      updateReply(comment.localId, reply.localId, {
        mode: 'default',
        text: reply.newText,
        author: reply.author,
      }),
    );
  } catch (err) {
    /* eslint-disable-next-line no-console */
    console.error(err);
    store.dispatch(
      updateReply(comment.localId, reply.localId, {
        mode: 'save_error',
      }),
    );
  }
}

async function deleteCommentReply(
  comment: Comment,
  reply: CommentReply,
  store: Store,
) {
  store.dispatch(
    updateReply(comment.localId, reply.localId, {
      mode: 'deleting',
    }),
  );

  try {
    store.dispatch(deleteReply(comment.localId, reply.localId));
  } catch (err) {
    store.dispatch(
      updateReply(comment.localId, reply.localId, {
        mode: 'delete_error',
      }),
    );
  }
}

export interface CommentReplyProps {
  comment: Comment;
  reply: CommentReply;
  store: Store;
  user: Author | null;
  isFocused: boolean;
}

export default class CommentReplyComponent extends React.Component<CommentReplyProps> {
  renderEditing(): React.ReactFragment {
    const { comment, reply, store, isFocused } = this.props;

    const onChangeText = (value: string) => {
      store.dispatch(
        updateReply(comment.localId, reply.localId, {
          newText: value,
        }),
      );
    };

    const onSave = async (e: React.FormEvent) => {
      e.preventDefault();
      await saveCommentReply(comment, reply, store);
    };

    const onCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateReply(comment.localId, reply.localId, {
          mode: 'default',
          newText: reply.text,
        }),
      );
    };

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <form onSubmit={onSave}>
          <TextArea
            className="comment-reply__input"
            value={reply.newText}
            onChange={onChangeText}
          />
          <div className="comment-reply__actions">
            <button
              type="submit"
              disabled={reply.newText.length === 0}
              className="comment-reply__button comment-reply__button--primary"
            >
              {gettext('Save')}
            </button>
            <button
              type="button"
              className="comment-reply__button"
              onClick={onCancel}
            >
              {gettext('Cancel')}
            </button>
          </div>
        </form>
      </>
    );
  }

  renderSaving(): React.ReactFragment {
    const { reply, store, isFocused } = this.props;

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <p className="comment-reply__text">{reply.text}</p>
        <div className="comment-reply__progress">{gettext('Saving...')}</div>
      </>
    );
  }

  renderSaveError(): React.ReactFragment {
    const { comment, reply, store, isFocused } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await saveCommentReply(comment, reply, store);
    };

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <p className="comment-reply__text">{reply.text}</p>
        <div className="comment-reply__error">
          {gettext('Save error')}
          <button
            type="button"
            className="comment-reply__button"
            onClick={onClickRetry}
          >
            {gettext('Retry')}
          </button>
        </div>
      </>
    );
  }

  renderDeleteConfirm(): React.ReactFragment {
    const { comment, reply, store, isFocused } = this.props;

    const onClickDelete = async (e: React.MouseEvent) => {
      e.preventDefault();

      await deleteCommentReply(comment, reply, store);
    };

    const onClickCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateReply(comment.localId, reply.localId, {
          mode: 'default',
        }),
      );
    };

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <p className="comment-reply__text">{reply.text}</p>
        <div className="comment-reply__confirm-delete">
          {gettext('Are you sure?')}
          <button
            type="button"
            className="comment-reply__button"
            onClick={onClickCancel}
          >
            {gettext('Cancel')}
          </button>
          <button
            type="button"
            className="comment-reply__button comment-reply__button--primary"
            onClick={onClickDelete}
          >
            {gettext('Delete')}
          </button>
        </div>
      </>
    );
  }

  renderDeleting(): React.ReactFragment {
    const { reply, store, isFocused } = this.props;

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <p className="comment-reply__text">{reply.text}</p>
        <div className="comment-reply__progress">{gettext('Deleting')}</div>
      </>
    );
  }

  renderDeleteError(): React.ReactFragment {
    const { comment, reply, store, isFocused } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await deleteCommentReply(comment, reply, store);
    };

    const onClickCancel = async (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateReply(comment.localId, reply.localId, {
          mode: 'default',
        }),
      );
    };

    return (
      <>
        <CommentHeader commentReply={reply} store={store} focused={isFocused} />
        <p className="comment-reply__text">{reply.text}</p>
        <div className="comment-reply__error">
          {gettext('Delete error')}
          <button
            type="button"
            className="comment-reply__button"
            onClick={onClickCancel}
          >
            {gettext('Cancel')}
          </button>
          <button
            type="button"
            className="comment-reply__button"
            onClick={onClickRetry}
          >
            {gettext('Retry')}
          </button>
        </div>
      </>
    );
  }

  renderDefault(): React.ReactFragment {
    const { comment, reply, store, isFocused } = this.props;

    // Show edit/delete buttons if this reply was authored by the current user
    let onEdit;
    let onDelete;
    if (
      reply.author === null ||
      (this.props.user && this.props.user.id === reply.author.id)
    ) {
      onEdit = () => {
        store.dispatch(
          updateReply(comment.localId, reply.localId, {
            mode: 'editing',
            newText: reply.text,
          }),
        );
      };

      onDelete = () => {
        store.dispatch(
          updateReply(comment.localId, reply.localId, {
            mode: 'delete_confirm',
          }),
        );
      };
    }

    let notice = '';
    if (!reply.remoteId || reply.text !== reply.originalText) {
      // Save the page to save this reply
      notice = gettext('Save the page to save this reply');
    }

    return (
      <>
        <CommentHeader
          commentReply={reply}
          store={store}
          onEdit={onEdit}
          onDelete={onDelete}
          focused={isFocused}
        />
        <p className="comment-reply__text">{reply.text}</p>
        {notice && (
          <div className="comment__notice-placeholder">
            <div className="comment__notice" role="status">
              <Icon name="info-circle" />
              {notice}
            </div>
          </div>
        )}
      </>
    );
  }

  render() {
    let inner: React.ReactFragment;

    switch (this.props.reply.mode) {
      case 'editing':
        inner = this.renderEditing();
        break;

      case 'saving':
        inner = this.renderSaving();
        break;

      case 'save_error':
        inner = this.renderSaveError();
        break;

      case 'delete_confirm':
        inner = this.renderDeleteConfirm();
        break;

      case 'deleting':
        inner = this.renderDeleting();
        break;

      case 'delete_error':
        inner = this.renderDeleteError();
        break;

      default:
        inner = this.renderDefault();
        break;
    }

    return (
      <li
        key={this.props.reply.localId}
        className={`comment-reply comment-reply--mode-${this.props.reply.mode}`}
        data-reply-id={this.props.reply.localId}
      >
        {inner}
      </li>
    );
  }
}
