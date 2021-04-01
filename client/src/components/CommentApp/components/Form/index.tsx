import React from 'react';

import type { Comment, CommentReply } from '../../state/comments';

interface PrefixedHiddenInputProps {
  prefix: string;
  value: number | string | null;
  fieldName: string;
}

function PrefixedHiddenInput({
  prefix,
  value,
  fieldName,
}: PrefixedHiddenInputProps) {
  return (
    <input
      type="hidden"
      name={`${prefix}-${fieldName}`}
      value={value === null ? '' : value}
      id={`id_${prefix}-${fieldName}`}
    />
  );
}

export interface CommentReplyFormComponentProps {
  reply: CommentReply;
  prefix: string;
  formNumber: number;
}

export function CommentReplyFormComponent({
  reply,
  formNumber,
  prefix,
}: CommentReplyFormComponentProps) {
  const fullPrefix = `${prefix}-${formNumber}`;
  return (
    <fieldset>
      <PrefixedHiddenInput
        fieldName="DELETE"
        value={reply.deleted ? 1 : ''}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="id"
        value={reply.remoteId}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="text"
        value={reply.text}
        prefix={fullPrefix}
      />
    </fieldset>
  );
}

export interface CommentReplyFormSetProps {
  replies: CommentReply[];
  prefix: string;
  remoteReplyCount: number;
}

export function CommentReplyFormSetComponent({
  replies,
  prefix,
  remoteReplyCount,
}: CommentReplyFormSetProps) {
  const fullPrefix = `${prefix}-replies`;

  const commentForms = replies.map((reply, formNumber) => (
    <CommentReplyFormComponent
      key={reply.localId}
      formNumber={formNumber}
      reply={reply}
      prefix={fullPrefix}
    />
  ));

  return (
    <>
      <PrefixedHiddenInput
        fieldName="TOTAL_FORMS"
        value={replies.length}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="INITIAL_FORMS"
        value={remoteReplyCount}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="MIN_NUM_FORMS"
        value="0"
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="MAX_NUM_FORMS"
        value=""
        prefix={fullPrefix}
      />
      {commentForms}
    </>
  );
}

export interface CommentFormProps {
  comment: Comment;
  formNumber: number;
  prefix: string;
}

export function CommentFormComponent({
  comment,
  formNumber,
  prefix,
}: CommentFormProps) {
  const fullPrefix = `${prefix}-${formNumber}`;

  return (
    <fieldset>
      <PrefixedHiddenInput
        fieldName="DELETE"
        value={comment.deleted ? 1 : ''}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="resolved"
        value={comment.resolved ? 1 : ''}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="id"
        value={comment.remoteId}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="contentpath"
        value={comment.contentpath}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="text"
        value={comment.text}
        prefix={fullPrefix}
      />
      <PrefixedHiddenInput
        fieldName="position"
        value={comment.position}
        prefix={fullPrefix}
      />
      <CommentReplyFormSetComponent
        replies={Array.from(comment.replies.values())}
        prefix={fullPrefix}
        remoteReplyCount={comment.remoteReplyCount}
      />
    </fieldset>
  );
}

export interface CommentFormSetProps {
  comments: Comment[];
  remoteCommentCount: number;
}

export function CommentFormSetComponent({
  comments,
  remoteCommentCount,
}: CommentFormSetProps) {
  const prefix = 'comments';

  const commentForms = comments.map((comment, formNumber) => (
    <CommentFormComponent
      key={comment.localId}
      comment={comment}
      formNumber={formNumber}
      prefix={prefix}
    />
  ));

  return (
    <>
      <PrefixedHiddenInput
        fieldName="TOTAL_FORMS"
        value={comments.length}
        prefix={prefix}
      />
      <PrefixedHiddenInput
        fieldName="INITIAL_FORMS"
        value={remoteCommentCount}
        prefix={prefix}
      />
      <PrefixedHiddenInput
        fieldName="MIN_NUM_FORMS"
        value="0"
        prefix={prefix}
      />
      <PrefixedHiddenInput fieldName="MAX_NUM_FORMS" value="" prefix={prefix} />
      {commentForms}
    </>
  );
}
