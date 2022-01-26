let nextCommentId = 1;
let nextReplyId = 1;

export function getNextCommentId() {
  return nextCommentId++;
}

export function getNextReplyId() {
  return nextReplyId++;
}
