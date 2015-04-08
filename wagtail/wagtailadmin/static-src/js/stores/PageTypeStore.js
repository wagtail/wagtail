import isParent from '../utils/common';
import AppDispatcher from '../dispatcher';
import EventEmitter from 'events';
import PageTypeActions from '../actions/PageTypeActions';


class BasePageTypeStore extends EventEmitter {
    constructor () {
        super();
        this.items = [];
    }
    add(payload) {

    }
    remove(payload) {

    }
    populate(payload) {
        this.items = payload.data;
        this.emit('change');
    }
    beforeUpdate(payload) {

    }
    update(payload) {

    }
    getAll() {
        return this.items;
    }
    getTypeByName(name) {
        return this.items.find(i => { return name == i.type });
    }
}

const PageTypeStore = new BasePageTypeStore();

AppDispatcher.register( function( payload ) {
    switch( payload.eventName ) {
        case 'PAGETYPES_ADD':
            PageTypeStore.add(payload);
            break;
        case 'PAGETYPES_REMOVE':
            PageTypeStore.remove(payload);
            break;
        case 'PAGETYPES_POPULATE':
            PageTypeStore.populate(payload);
            break;
        case 'PAGETYPES_FETCH_START':
            PageTypeStore.beforeUpdate(payload);
            break;
        case 'PAGETYPES_FETCH_COMPLETE':
            PageTypeStore.update(payload);
            break;
    }

    return true;
});

export default PageTypeStore;
