import isParent from '../utils/common';
import AppDispatcher from '../dispatcher';
import EventEmitter from 'events';
import ColumnViewActions from '../actions/ColumnViewActions';


class BaseColumnViewStore extends EventEmitter {
    constructor () {
        super();
        this.stack = [];
        this.data = {};
        this.initalStackData = {};
    }

    update(payload) {
        const stack = this.stack;
        const targetColumn = stack[column];
        const draggedItem = stack[newItem.column].children[newItem.id];

        if (isParent(targetItem, draggedItem)) {
            // TODO: Fire a message if user attempts to drag node into child.
            return;
        }

        // Don't proceed if the child is a direct descendant.
        if ( targetItem.children.indexOf(draggedItem) > -1) {
            return;
        }

        // Remove draggedItem from the stack...
        if (draggedItem) {
            stack[newItem.column].children.splice(newItem.id, 1);
        }

        targetColumn.children[afterId].children.splice(targetColumn.children[afterId].children.length, 0, draggedItem);


        stack[column] = targetColumn;
        this.stack = stack;
        this.emit('change');
    }

    move(payload) {
        // TODO
        this.emit('change');
    }

    show(payload) {
        const stack = this.stack;
        const { node, index, level } = payload;

        const indexOfNode = stack.indexOf(node);

        if (stack.length > level && indexOfNode < stack.length) {
            while (stack.length > level + 1) {
                stack.pop();
            }
        }

        // Only allow items to be pushed onto the stack once.
        if (indexOfNode < 0) {
            stack.push(node);
        }

        this.stack = stack;
        this.emit('change');
    }

    clear(payload) {
        this.stack = [this._initialStackData];
        this.emit('change');
    }

    populate(payload) {
        const { data } = payload;


        function createLinkedList(collection) {
            if (!collection.children) {
                collection.children = [];
            }

            if (!collection.status) {
                collection.status = "draft";
            }

            collection.children.forEach(function(model) {

                if (!model.children) {
                    model.children = [];
                }

                if (!model.parent) {
                    model.parent = collection;
                }

                if (!model.status) {
                    model.status = "draft";
                }

                if (model.children.length > 0){
                    createLinkedList(model);
                }
            });
        };

        createLinkedList(data);
        console.log(data);

        this.data = data;
        this.stack = [];
        // Push the root node on the stack;
        this.stack.push(this.data);
        this._initialStackData = this.stack[0];
        this.emit('change');
    }

    getAll() {
        return this.data;
    }

    getStack() {
        return this.stack;
    }

    setLoadingState(payload) {
        const { node } = payload;

        node.loading = true;
        this.emit('change');
    }

    updateNode(payload) {
        const { node } = payload;

        node.loading = false;
        node.children = payload.data;

        this.emit('change');
    }

    create(payload) {
        const { target, typeObject, index } = payload;

        target.children.push({
            name: "New page",
            status: "draft",
            type: typeObject.type,
            parent: target
        });

        this.emit('change');
    }

    remove(payload) {
        const { target } = payload;

        // No deleting the root node, thank you very much!
        if (!target.parent) {
            return;
        }

        var index = target.parent.children.indexOf(target);
        target.parent.children.splice(index, 1);

        this.emit('change');
    }

    showModal(payload) {
        this.modal = true;
        this.emit('change');
    }

    dismissModal(payload) {
        this.modal = false;
        this.emit('change');
    }

    getModal() {
        return this.modal;
    }
}


const ColumnViewStore = new BaseColumnViewStore();



AppDispatcher.register( function( payload ) {
    switch( payload.eventName ) {
        case 'CARD_SHOW':
            ColumnViewStore.show(payload);
            break;
        case 'CARD_MOVE':
            ColumnViewStore.move(payload);
            break;
        case 'CARD_CLEAR_STACK':
            ColumnViewStore.clear(payload);
            break;
        case 'CARD_UPDATE':
            ColumnViewStore.update(payload);
            break;
        case 'CARD_POPULATE':
            ColumnViewStore.populate(payload);
            break;
        case 'CARD_FETCH_START':
            ColumnViewStore.setLoadingState(payload);
            break;
        case 'CARD_FETCH_COMPLETE':
            ColumnViewStore.updateNode(payload);
            break;
        case 'CARD_MODAL':
            ColumnViewStore.showModal(payload);
            break;
        case 'CARD_MODAL_DISMISS':
            ColumnViewStore.dismissModal(payload);
            break;
        case 'CARD_CREATE':
            ColumnViewStore.create(payload);
            break;
        case 'CARD_REMOVE':
            ColumnViewStore.remove(payload);
            break;
    }

    return true;
});



export default ColumnViewStore;
