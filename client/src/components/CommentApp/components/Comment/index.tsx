/* eslint-disable react/prop-types */

import React from 'react';
import ReactDOM from 'react-dom';

import type { Store } from '../../state';
import { Author, Comment, newCommentReply } from '../../state/comments';
import {
  updateComment,
  deleteComment,
  setFocusedComment,
  addReply
} from '../../actions/comments';
import { LayoutController } from '../../utils/layout';
import { getNextReplyId } from '../../utils/sequences';
import CommentReplyComponent from '../CommentReply';
import type { TranslatableStrings } from '../../main';
import { CommentHeader }  from '../CommentHeader';

async function saveComment(comment: Comment, store: Store) {
  store.dispatch(
    updateComment(comment.localId, {
      mode: 'saving',
    })
  );

  try {
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'default',
        text: comment.newText,
        remoteId: comment.remoteId,
        author: comment.author,
        date: comment.date,
      })
    );
  } catch (err) {
    /* eslint-disable-next-line no-console */
    console.error(err);
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'save_error',
      })
    );
  }
}

async function doDeleteComment(comment: Comment, store: Store) {
  store.dispatch(
    updateComment(comment.localId, {
      mode: 'deleting',
    })
  );

  try {
    store.dispatch(deleteComment(comment.localId));
  } catch (err) {
    /* eslint-disable-next-line no-console */
    console.error(err);
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'delete_error',
      })
    );
  }
}

function resolveComment(comment: Comment, store: Store) {
  store.dispatch(
    updateComment(comment.localId, {
      resolved: true,
    })
  );
}

export interface CommentProps {
  store: Store;
  comment: Comment;
  isFocused: boolean;
  layout: LayoutController;
  user: Author | null;
  strings: TranslatableStrings;
}

export default class CommentComponent extends React.Component<CommentProps> {
  renderReplies({ hideNewReply = false } = {}): React.ReactFragment {
    const { comment, isFocused, store, user, strings } = this.props;

    if (!comment.remoteId) {
      // Hide replies UI if the comment itself isn't saved yet
      return <></>;
    }

    const onChangeNewReply = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          newReply: e.target.value,
        })
      );
    };

    const sendReply = async (e: React.FormEvent) => {
      e.preventDefault();

      const replyId = getNextReplyId();
      const reply = newCommentReply(replyId, user, Date.now(), {
        text: comment.newReply,
        mode: 'default',
      });
      store.dispatch(addReply(comment.localId, reply));

      store.dispatch(
        updateComment(comment.localId, {
          newReply: '',
        })
      );
    };

    const onClickCancelReply = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          newReply: '',
        })
      );
    };

    const replies: React.ReactNode[] = [];
    let replyBeingEdited = false;
    for (const reply of comment.replies.values()) {
      if (reply.mode === 'saving' || reply.mode === 'editing') {
        replyBeingEdited = true;
      }

      if (!reply.deleted) {
        replies.push(
          <CommentReplyComponent
            key={reply.localId}
            store={store}
            user={user}
            comment={comment}
            reply={reply}
            strings={strings}
          />
        );
      }
    }

    // Hide new reply if a reply is being edited as well
    const newReplyHidden = hideNewReply || replyBeingEdited;

    let replyActions = <></>;
    if (!newReplyHidden && isFocused && comment.newReply.length > 0) {
      replyActions = (
        <div className="comment__reply-actions">
          <button
            type="submit"
            className="comment__button comment__button--primary"
          >
            {strings.REPLY}
          </button>
          <button
            type="button"
            onClick={onClickCancelReply}
            className="comment__button"
          >
            {strings.CANCEL}
          </button>
        </div>
      );
    }

    let replyTextarea = <></>;
    if (!newReplyHidden && (isFocused || comment.newReply)) {
      replyTextarea = (
        <textarea
          className="comment__reply-input"
          placeholder="Enter your reply..."
          value={comment.newReply}
          onChange={onChangeNewReply}
          style={{ resize: 'none' }}
        />
      );
    }

    return (
      <>
        <ul className="comment__replies">{replies}</ul>
        <form onSubmit={sendReply}>
          {replyTextarea}
          {replyActions}
        </form>
      </>
    );
  }

  renderCreating(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    const onChangeText = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          newText: e.target.value,
        })
      );
    };

    const onSave = async (e: React.FormEvent) => {
      e.preventDefault();
      await saveComment(comment, store);
    };

    const onCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(deleteComment(comment.localId));
    };

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <form onSubmit={onSave}>
          <textarea
            className="comment__input"
            value={comment.newText}
            onChange={onChangeText}
            style={{ resize: 'none' }}
            placeholder="Enter your comments..."
          />
          <div className="comment__actions">
            <button
              type="submit"
              className="comment__button comment__button--primary"
            >
              {strings.COMMENT}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="comment__button"
            >
              {strings.CANCEL}
            </button>
          </div>
        </form>
      </>
    );
  }

  renderEditing(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    const onChangeText = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          newText: e.target.value,
        })
      );
    };

    const onSave = async (e: React.FormEvent) => {
      e.preventDefault();

      await saveComment(comment, store);
    };

    const onCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          mode: 'default',
          newText: comment.text,
        })
      );
    };

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <form onSubmit={onSave}>
          <textarea
            className="comment__input"
            value={comment.newText}
            onChange={onChangeText}
            style={{ resize: 'none' }}
          />
          <div className="comment__actions">
            <button
              type="submit"
              className="comment__button comment__button--primary"
            >
              {strings.SAVE}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="comment__button"
            >
              {strings.CANCEL}
            </button>
          </div>
        </form>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderSaving(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__progress">{strings.SAVING}</div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderSaveError(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await saveComment(comment, store);
    };

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <p className="comment__text">{comment.text}</p>
        {this.renderReplies({ hideNewReply: true })}
        <div className="comment__error">
          {strings.SAVE_ERROR}
          <button
            type="button"
            className="comment__button"
            onClick={onClickRetry}
          >
            {strings.RETRY}
          </button>
        </div>
      </>
    );
  }

  renderDeleteConfirm(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    const onClickDelete = async (e: React.MouseEvent) => {
      e.preventDefault();

      await doDeleteComment(comment, store);
    };

    const onClickCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          mode: 'default',
        })
      );
    };

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__confirm-delete">
          {strings.CONFIRM_DELETE_COMMENT}
          <button
            type="button"
            className="comment__button comment__button--red"
            onClick={onClickDelete}
          >
            {strings.DELETE}
          </button>
          <button
            type="button"
            className="comment__button"
            onClick={onClickCancel}
          >
            {strings.CANCEL}
          </button>
        </div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderDeleting(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__progress">{strings.DELETING}</div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderDeleteError(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await doDeleteComment(comment, store);
    };

    const onClickCancel = async (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          mode: 'default',
        })
      );
    };

    return (
      <>
        <CommentHeader commentReply={comment} store={store} strings={strings} />
        <p className="comment__text">{comment.text}</p>
        {this.renderReplies({ hideNewReply: true })}
        <div className="comment__error">
          {strings.DELETE_ERROR}
          <button
            type="button"
            className="comment__button"
            onClick={onClickCancel}
          >
            {strings.CANCEL}
          </button>
          <button
            type="button"
            className="comment__button"
            onClick={onClickRetry}
          >
            {strings.RETRY}
          </button>
        </div>
      </>
    );
  }

  renderDefault(): React.ReactFragment {
    const { comment, store, strings } = this.props;

    // Show edit/delete buttons if this comment was authored by the current user
    let onEdit;
    let onDelete;
    if (comment.author === null || this.props.user && this.props.user.id === comment.author.id) {
      onEdit = () => {
        store.dispatch(
          updateComment(comment.localId, {
            mode: 'editing',
            newText: comment.text,
          })
        );
      };

      onDelete = () => {
        store.dispatch(
          updateComment(comment.localId, {
            mode: 'delete_confirm',
          })
        );
      };
    }

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          strings={strings}
          onResolve={resolveComment}
          onEdit={onEdit}
          onDelete={onDelete}
        />
        <p className="comment__text">{comment.text}</p>
        {this.renderReplies()}
      </>
    );
  }

  render() {
    let inner: React.ReactFragment;

    switch (this.props.comment.mode) {
    case 'creating':
      inner = this.renderCreating();
      break;

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

    const onClick = () => {
      this.props.store.dispatch(setFocusedComment(this.props.comment.localId));
    };

    const onDoubleClick = () => {
      this.props.store.dispatch(setFocusedComment(this.props.comment.localId, { updatePinnedComment: true }));
    };

    const top = this.props.layout.getCommentPosition(
      this.props.comment.localId
    );
    const right = this.props.isFocused ? 50 : 0;
    return (
      <li
        key={this.props.comment.localId}
        className={`comment comment--mode-${this.props.comment.mode} ${this.props.isFocused ? 'comment--focused' : ''}`}
        style={{
          position: 'absolute',
          top: `${top}px`,
          right: `${right}px`,
        }}
        data-comment-id={this.props.comment.localId}
        onClick={onClick}
        onDoubleClick={onDoubleClick}
      >
        {inner}
      </li>
    );
  }

  componentDidMount() {
    const element = ReactDOM.findDOMNode(this);

    if (element instanceof HTMLElement) {
      // If this is a new comment, focus in the edit box
      if (this.props.comment.mode === 'creating') {
        const textAreaElement = element.querySelector('textarea');

        if (textAreaElement instanceof HTMLTextAreaElement) {
          textAreaElement.focus();
        }
      }

      this.props.layout.setCommentElement(this.props.comment.localId, element);
      this.props.layout.setCommentHeight(
        this.props.comment.localId,
        element.offsetHeight
      );
    }
  }

  componentWillUnmount() {
    this.props.layout.setCommentElement(this.props.comment.localId, null);
  }

  componentDidUpdate() {
    const element = ReactDOM.findDOMNode(this);

    // Keep height up to date so that other comments will be moved out of the way
    if (element instanceof HTMLElement) {
      this.props.layout.setCommentHeight(
        this.props.comment.localId,
        element.offsetHeight
      );
    }
  }
}
