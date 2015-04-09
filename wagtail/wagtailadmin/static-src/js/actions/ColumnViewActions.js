import PageService from '../services/PageService';
import AppDispatcher from '../dispatcher';


const ColumnViewActions = {
    updateCard(targetItem, afterId, column, newItem) {
        AppDispatcher.dispatch({
            eventName: 'CARD_UPDATE',
            targetItem,
            afterId,
            column,
            newItem
        });
    },
    move(targetItem, afterId, column, newItem) {
        AppDispatcher.dispatch({
            eventName: 'CARD_MOVE',
            targetItem,
            afterId,
            column,
            newItem
        });
    },
    clearStack() {
        AppDispatcher.dispatch({
            eventName: 'CARD_CLEAR_STACK'
        });
    },
    show(node, index, level) {
        AppDispatcher.dispatch({
            eventName: 'CARD_SHOW',
            node,
            index,
            level
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
    leave() {
        AppDispatcher.dispatch({
            eventName: 'CARD_LEAVE'
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
    removeCard(target) {
        AppDispatcher.dispatch({
            eventName: 'CARD_REMOVE',
            target
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
            data: data,
            node: node,
            url: url
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
