import { initCommentsApp } from 'wagtail-comment-frontend';
import { STRINGS } from '../../config/wagtailConfig';

function initComments(element, author, initialComments, addAnnotatableSections) {
    return initCommentsApp(element, author, initialComments, addAnnotatableSections, STRINGS);
}

export default {
    initComments
}