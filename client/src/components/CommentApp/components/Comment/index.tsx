import React from 'react';
import ReactDOM from 'react-dom';
import FocusTrap from 'focus-trap-react';

import { gettext } from '../../../../utils/gettext';
import Icon from '../../../Icon/Icon';
import type { Store } from '../../state';
import { Author, Comment, newCommentReply } from '../../state/comments';
import {
  updateComment,
  deleteComment,
  resolveComment,
  setFocusedComment,
  addReply,
} from '../../actions/comments';
import { LayoutController } from '../../utils/layout';
import { getNextReplyId } from '../../utils/sequences';
import CommentReplyComponent from '../CommentReply';
import { CommentHeader } from '../CommentHeader';
import TextArea from '../TextArea';

async function saveComment(comment: Comment, store: Store) {
  store.dispatch(
    updateComment(comment.localId, {
      mode: 'saving',
    }),
  );

  try {
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'default',
        text: comment.newText,
        remoteId: comment.remoteId,
        author: comment.author,
        date: comment.date,
      }),
    );
  } catch (err) {
    /* eslint-disable-next-line no-console */
    console.error(err);
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'save_error',
      }),
    );
  }
}

async function doDeleteComment(comment: Comment, store: Store) {
  store.dispatch(
    updateComment(comment.localId, {
      mode: 'deleting',
    }),
  );

  try {
    store.dispatch(deleteComment(comment.localId));
  } catch (err) {
    /* eslint-disable-next-line no-console */
    console.error(err);
    store.dispatch(
      updateComment(comment.localId, {
        mode: 'delete_error',
      }),
    );
  }
}

function doResolveComment(comment: Comment, store: Store) {
  store.dispatch(resolveComment(comment.localId));
}

export interface CommentProps {
  store: Store;
  comment: Comment;
  isFocused: boolean;
  forceFocus: boolean;
  isVisible: boolean;
  layout: LayoutController;
  user: Author | null;
}

export default class CommentComponent extends React.Component<CommentProps> {
  renderReplies({ hideNewReply = false } = {}): React.ReactFragment | null {
    const { comment, isFocused, store, user } = this.props;

    if (!comment.remoteId) {
      // Hide replies UI if the comment itself isn't saved yet
      return null;
    }

    const onChangeNewReply = (value: string) => {
      store.dispatch(
        updateComment(comment.localId, {
          newReply: value,
        }),
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
        }),
      );
    };

    const onClickCancelReply = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          newReply: '',
        }),
      );

      store.dispatch(setFocusedComment(null));

      // Stop the event bubbling so that the comment isn't immediately refocused
      e.stopPropagation();
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
            isFocused={isFocused}
          />,
        );
      }
    }

    // Hide new reply if a reply is being edited as well
    const newReplyHidden = hideNewReply || replyBeingEdited;

    let replyForm;
    if (!newReplyHidden && (isFocused || comment.newReply)) {
      replyForm = (
        <form onSubmit={sendReply}>
          <TextArea
            className="comment__reply-input"
            placeholder={gettext('Enter your reply...')}
            value={comment.newReply}
            onChange={onChangeNewReply}
          />
          <div className="comment__reply-actions">
            <button
              disabled={comment.newReply.length === 0}
              type="submit"
              className="comment__button comment__button--primary"
            >
              {gettext('Reply')}
            </button>
            <button
              type="button"
              onClick={onClickCancelReply}
              className="comment__button"
            >
              {gettext('Cancel')}
            </button>
          </div>
        </form>
      );
    } else if (replies.length === 0) {
      // If there is no form, or replies, don't add any elements to the dom
      // This is in case there is a warning after the comment, some special styling
      // is added if that element is that last child so we can't have any hidden elements here.
      return null;
    }

    return (
      <>
        <ul className="comment__replies">{replies}</ul>
        {replyForm}
      </>
    );
  }

  renderCreating(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    const onChangeText = (value: string) => {
      store.dispatch(
        updateComment(comment.localId, {
          newText: value,
        }),
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

    const descriptionId = `comment-description-${comment.localId}`;

    return (
      <>
        <CommentHeader
          descriptionId={descriptionId}
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <form onSubmit={onSave}>
          <TextArea
            focusTarget={isFocused}
            className="comment__input"
            value={comment.newText}
            onChange={onChangeText}
            placeholder={gettext('Enter your comments...')}
            additionalAttributes={{
              'aria-describedby': descriptionId,
            }}
          />
          <div className="comment__actions">
            <button
              disabled={comment.newText.length === 0}
              type="submit"
              className="comment__button comment__button--primary"
            >
              {gettext('Comment')}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="comment__button"
            >
              {gettext('Cancel')}
            </button>
          </div>
        </form>
      </>
    );
  }

  renderEditing(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    const onChangeText = (value: string) => {
      store.dispatch(
        updateComment(comment.localId, {
          newText: value,
        }),
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
        }),
      );
    };

    const descriptionId = `comment-description-${comment.localId}`;

    return (
      <>
        <CommentHeader
          descriptionId={descriptionId}
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <form onSubmit={onSave}>
          <TextArea
            focusTarget={isFocused}
            className="comment__input"
            value={comment.newText}
            additionalAttributes={{
              'aria-describedby': descriptionId,
            }}
            onChange={onChangeText}
          />
          <div className="comment__actions">
            <button
              disabled={comment.newText.length === 0}
              type="submit"
              className="comment__button comment__button--primary"
            >
              {gettext('Save')}
            </button>
            <button
              type="button"
              onClick={onCancel}
              className="comment__button"
            >
              {gettext('Cancel')}
            </button>
          </div>
        </form>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderSaving(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__progress">{gettext('Saving...')}</div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderSaveError(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await saveComment(comment, store);
    };

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        {this.renderReplies({ hideNewReply: true })}
        <div className="comment__error">
          {gettext('Save error')}
          <button
            type="button"
            className="comment__button"
            onClick={onClickRetry}
          >
            {gettext('Retry')}
          </button>
        </div>
      </>
    );
  }

  renderDeleteConfirm(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    const onClickDelete = async (e: React.MouseEvent) => {
      e.preventDefault();

      await doDeleteComment(comment, store);
    };

    const onClickCancel = (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          mode: 'default',
        }),
      );
    };

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__confirm-delete">
          {gettext('Are you sure?')}
          <button
            type="button"
            className="comment__button"
            onClick={onClickCancel}
          >
            {gettext('Cancel')}
          </button>
          <button
            type="button"
            className="comment__button comment__button--primary"
            onClick={onClickDelete}
          >
            {gettext('Delete')}
          </button>
        </div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderDeleting(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        <div className="comment__progress">{gettext('Deleting')}</div>
        {this.renderReplies({ hideNewReply: true })}
      </>
    );
  }

  renderDeleteError(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    const onClickRetry = async (e: React.MouseEvent) => {
      e.preventDefault();

      await doDeleteComment(comment, store);
    };

    const onClickCancel = async (e: React.MouseEvent) => {
      e.preventDefault();

      store.dispatch(
        updateComment(comment.localId, {
          mode: 'default',
        }),
      );
    };

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        {this.renderReplies({ hideNewReply: true })}
        <div className="comment__error">
          {gettext('Delete error')}
          <button
            type="button"
            className="comment__button"
            onClick={onClickCancel}
          >
            {gettext('Cancel')}
          </button>
          <button
            type="button"
            className="comment__button"
            onClick={onClickRetry}
          >
            {gettext('Retry')}
          </button>
        </div>
      </>
    );
  }

  renderDefault(): React.ReactFragment {
    const { comment, store, isFocused } = this.props;

    // Show edit/delete buttons if this comment was authored by the current user
    let onEdit;
    let onDelete;
    if (
      comment.author === null ||
      (this.props.user && this.props.user.id === comment.author.id)
    ) {
      onEdit = () => {
        store.dispatch(
          updateComment(comment.localId, {
            mode: 'editing',
            newText: comment.text,
          }),
        );
      };

      onDelete = () => {
        store.dispatch(
          updateComment(comment.localId, {
            mode: 'delete_confirm',
          }),
        );
      };
    }

    let notice = '';
    if (!comment.remoteId) {
      // Save the page to add this comment
      notice = gettext('Save the page to add this comment');
    } else if (comment.text !== comment.originalText) {
      // Save the page to save this comment
      notice = gettext('Save the page to save this comment');
    }

    return (
      <>
        <CommentHeader
          commentReply={comment}
          store={store}
          onResolve={doResolveComment}
          onEdit={onEdit}
          onDelete={onDelete}
          focused={isFocused}
        />
        <p className="comment__text">{comment.text}</p>
        {notice && (
          <div className="comment__notice-placeholder">
            <div className="comment__notice" role="status">
              <Icon name="info-circle" />
              {notice}
            </div>
          </div>
        )}
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
      this.props.store.dispatch(
        setFocusedComment(this.props.comment.localId, {
          updatePinnedComment: false,
          forceFocus: this.props.isFocused && this.props.forceFocus,
        }),
      );
    };

    const onDoubleClick = () => {
      this.props.store.dispatch(
        setFocusedComment(this.props.comment.localId, {
          updatePinnedComment: true,
          forceFocus: true,
        }),
      );
    };

    const top = this.props.layout.getCommentPosition(
      this.props.comment.localId,
    );

    return (
      <FocusTrap
        focusTrapOptions={
          {
            preventScroll: true,
            clickOutsideDeactivates: true,
            onDeactivate: () => {
              this.props.store.dispatch(
                setFocusedComment(null, {
                  updatePinnedComment: true,
                  forceFocus: false,
                }),
              );
            },
            initialFocus: '[data-focus-target="true"]',
            delayFocus: false,
          } as any
        } // For some reason, the types for FocusTrap props don't yet include preventScroll.
        active={this.props.isFocused && this.props.forceFocus}
      >
        <li
          tabIndex={-1}
          data-focus-target={
            this.props.isFocused &&
            !['creating', 'editing'].includes(this.props.comment.mode)
          }
          key={this.props.comment.localId}
          className={`comment comment--mode-${this.props.comment.mode} ${
            this.props.isFocused ? 'comment--focused' : ''
          }`}
          style={{
            position: 'absolute',
            top: `${top}px`,
            display: this.props.isVisible ? 'block' : 'none',
          }}
          data-comment-id={this.props.comment.localId}
          onClick={onClick}
          onDoubleClick={onDoubleClick}
        >
          {inner}
        </li>
      </FocusTrap>
    );
  }

  componentDidMount() {
    // eslint-disable-next-line react/no-find-dom-node
    const element = ReactDOM.findDOMNode(this);

    if (element instanceof HTMLElement) {
      this.props.layout.setCommentElement(this.props.comment.localId, element);

      if (this.props.isVisible) {
        this.props.layout.setCommentHeight(
          this.props.comment.localId,
          element.offsetHeight,
        );
      }
    }
  }

  componentWillUnmount() {
    this.props.layout.setCommentElement(this.props.comment.localId, null);
  }

  componentDidUpdate() {
    // eslint-disable-next-line react/no-find-dom-node
    const element = ReactDOM.findDOMNode(this);

    // Keep height up to date so that other comments will be moved out of the way
    if (this.props.isVisible && element instanceof HTMLElement) {
      this.props.layout.setCommentHeight(
        this.props.comment.localId,
        element.offsetHeight,
      );
    }
  }
}
