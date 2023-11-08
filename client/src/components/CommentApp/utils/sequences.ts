let nextCommentId = 1;
let nextReplyId = 1;

export function getNextCommentId() {
  nextCommentId += 1;
  return nextCommentId;
}

export function getNextReplyId() {
  nextReplyId += 1;
  return nextReplyId;
}
