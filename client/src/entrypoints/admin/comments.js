import comments, { initAddCommentButton } from '../../components/CommentApp/comments';

/**
 * Entry point loaded when the comments system is in use.
 */
// Expose module as a global.
window.comments = comments;


document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-comment-add]').forEach(initAddCommentButton);
});
