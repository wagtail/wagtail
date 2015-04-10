import PageService from '../services/PageService';
import AppDispatcher from '../dispatcher';


const ColumnViewActions = {
    dropCard(targetId, sourceId) {
        AppDispatcher.dispatch({
            eventName: 'CARD_DROP',
            targetId,
            sourceId
        });
    },
    move(targetId, sourceId) {
        AppDispatcher.dispatch({
            eventName: 'CARD_MOVE',
            targetId,
            sourceId
        });
    },
    leave(targetId, sourceId) {
        AppDispatcher.dispatch({
            eventName: 'CARD_LEAVE',
            targetId,
            sourceId
        });
    },
    clearStack() {
        AppDispatcher.dispatch({
            eventName: 'CARD_CLEAR_STACK'
        });
    },
    show(node) {
        AppDispatcher.dispatch({
            eventName: 'CARD_SHOW',
            node
        });
    },
    showModal() {
        AppDispatcher.dispatch({
            eventName: 'CARD_MODAL'
        });
    },
    dismissModal() {
        AppDispatcher.dispatch({
            eventName: 'CARD_MODAL_DISMISS'
        });
    },
    createCard(payload) {
        const {target, typeObject, index } = payload;

        AppDispatcher.dispatch({
            eventName: 'CARD_CREATE',
            target,
            typeObject,
            index
        });
    },
    removeCard(id) {
        AppDispatcher.dispatch({
            eventName: 'CARD_REMOVE',
            id
        });
    },
    populate(data) {
        AppDispatcher.dispatch({
            eventName: 'CARD_POPULATE',
            data,
        });
    },
    fetch(payload) {
        const { url, node } = payload;
        const service = new PageService();

        AppDispatcher.dispatch({
            eventName: 'CARD_FETCH_START',
            node: node,
            url: url
        });

        service.fetchChild(url, node, ColumnViewActions.fetchComplete);
    },
    fetchComplete(payload) {
        const { data, node, url } = payload;

        AppDispatcher.dispatch({
            eventName: 'CARD_FETCH_COMPLETE',
            data,
            node,
            url
        });
    },
    updateAttribute(payload) {
        const { node, attribute, value } = payload;

        AppDispatcher.dispatch({
            eventName: 'CARD_CHANGE_ATTRIBUTE',
            node,
            attribute,
            value
        });
    },
    setActive(payload) {
        AppDispatcher.dispatch({
            eventName: 'CARD_SET_ACTIVE',
            node,
            attribute,
            value
        });
    },
    hideExplorer(payload) {
        AppDispatcher.dispatch({
            eventName: 'EXPLORER_HIDE'
        });
    },
    showExplorer(payload) {
        AppDispatcher.dispatch({
            eventName: 'EXPLORER_SHOW'
        });
    },
    reset(payload) {
        AppDispatcher.dispatch({
            eventName: 'EXPLORER_RESET'
        });
    }
}

export default ColumnViewActions;
