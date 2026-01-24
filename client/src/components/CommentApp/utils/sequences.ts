let nextCommentId = 0;
let nextReplyId = 0;

export function getNextCommentId() {
  nextCommentId += 1;
  return nextCommentId;
}

export function getNextReplyId() {
  nextReplyId += 1;
  return nextReplyId;
}

export function resetCommentAndReplyIds() {
  nextCommentId = 0;
  nextReplyId = 0;
}
