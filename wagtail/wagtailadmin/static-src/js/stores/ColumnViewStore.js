// import isParent from '../utils/common';
import AppDispatcher from '../dispatcher';
import EventEmitter from 'events';
import generateUUID from '../utils/uuid';
import PageTypeStore from './PageTypeStore';


var lodash = require('lodash');

function visitBfs(node, func) {
    var q = [node];
    while (q.length > 0) {
        node = q.shift();
        var res = true;

        if (func) {
            res = func(node);
        }

        if (res === false) {
            return;
        }

        node.children.forEach(function (child) {
            q.push(child);
        });
    }
}


class BaseColumnViewStore extends EventEmitter {
    constructor () {
        super();
        this.stack = [];
        this.data = {};
        this._initalStackData = {};
    }


    drop(payload) {
        const { targetId, sourceId } = payload;
        const sourceNode = this.getById(sourceId);
        const currentParent = this.getById(sourceNode.parent);
        const newParent = this.getById(targetId);

        const isParent = function(parent, child) {
            if (parent.children.indexOf(child) > -1) {
                return true;
            }
            return parent.children.forEach(function(item) {
                isParent(item, child);
            });
        }.bind(this);

        // No dragging items into their parent nodes!
        if (isParent(sourceNode, newParent)) {
            return false;
        }

        var types = PageTypeStore.getTypeByName(newParent.type);
        var isValidType = types.subpage_types.indexOf(sourceNode.type) > -1;

        if (!isValidType) {
            return false;
        }

        var idx = currentParent.children.indexOf(sourceNode);
        currentParent.children.splice(idx, 1);

        sourceNode.parent = targetId;
        newParent.children.push(sourceNode);

        this.emit('change');
    }

    move(payload) {
        const { targetId, sourceId } = payload;
        const sourceNode = this.getById(sourceId);
        const targetNode = this.getById(targetId);
        var types = PageTypeStore.getTypeByName(targetNode.type);
        var isValidType = types.subpage_types.indexOf(sourceNode.type) > -1;
        targetNode.isValidDrop = isValidType;
        console.log(types, isValidType, targetNode);
        this.emit('change');
    }

    leave(payload) {
        const { targetId, sourceId } = payload;
        const targetNode = this.getById(targetId);
        targetNode.isValidDrop = undefined;
        this.emit('change');
    }

    show(payload) {
        const stack = this.stack;
        const nodeId = payload.node;
        const node = this.getById(nodeId);

        // Clear edits on the stack...
        const last = this.getLast();
        last.edit = false;

        // Determine path back to root...
        const getPathToRoot = function(item, arr) {
            if (!arr) arr = [];

            arr.push(item.id);

            if (item.parent) {
                var parentNode = this.getById(item.parent);
                getPathToRoot(parentNode, arr);
            }

            return arr;
        }.bind(this);

        const newStack = getPathToRoot(node);
        newStack.reverse();

        var stackIndex = this.stack.indexOf(node.id);

        if (stackIndex === this.stack.length-1) {
            newStack.pop();
        }

        this.stack = newStack;
        this.emit('change');
    }

    clear(payload) {
        this.stack = [this._initialStackData.id];
        this.emit('change');
    }

    parseNode(node, parent) {
        if (!node.children) {
            node.children = [];
        }

        if (!node.id) {
            node.id = generateUUID();
        }

        if (parent) {
            node.parent = parent.id;
        }

        if (!node.status) {
            node.status = 'draft';
        }

        if (!node.type) {
            node.type = 'site.StandardPage';
        }

        node.children = node.children.map(function(item) {
            return this.parseNode(item, node);
        }, this);

        return node;
    }

    populate(payload) {
        const { data } = payload;
        const newData = this.parseNode(data, null);

        this.data = newData;
        this.stack = [newData.id];
        this._initialStackData = this.stack[0];
        this.emit('change');
    }


    setLoadingState(payload) {
        const { node } = payload;
        var targetNode = this.getById(node);

        targetNode.loading = true;
        this.emit('change');
    }

    updateNode(payload) {
        const { node } = payload;
        var targetNode = this.getById(node);

        targetNode.loading = false;

        const newNodes = payload.data.map(function(item) {
            return this.parseNode(item, targetNode);
        }, this);

        targetNode.children = targetNode.children.concat(newNodes);

        this.emit('change');
    }

    updateAttribute(payload) {
        const { node, attribute, value } = payload;
        var targetNode = this.getById(node);


        node[attribute] = value;
        this.emit('change');
    }

    create(payload) {
        const { target, typeObject, index } = payload;
        var node = this.getById(target);

        node.children.push(this.parseNode({
            name: "New page",
            status: "draft",
            type: typeObject.type,
        }, node));

        this.emit('change');
    }

    getById(id) {
        var result;

        visitBfs(this.data, function(item) {
            if (item.id === id) {
                result = item;
                return false;
            }
        });

        return result;
    }

    remove(payload) {
        const { id } = payload;

        var targetNode = this.getById(id);

        // No deleting the root node, thank you very much!
        if (!targetNode.parent) {
            return;
        }

        const recursiveDelete = function(next) {
            var stackIndex = this.stack.indexOf(next.id);

            if (stackIndex > -1) {
                this.stack.splice(stackIndex, 1);
            }

            next.children.map(recursiveDelete);
            return null;
        }.bind(this);

        var res = targetNode.children.map(recursiveDelete);
        targetNode.children = [];

        var parentNode = this.getById(targetNode.parent);
        var index = parentNode.children.indexOf(targetNode);

        var stackIndex = this.stack.indexOf(id);

        if (stackIndex > -1) {
            this.stack.splice(stackIndex, 1);
        }

        parentNode.children.splice(index, 1);
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

    getAll() {
        return lodash.cloneDeep(this.data);
    }

    getStack() {
        return this.stack.map(function(id) {
            return this.getById(id);
        }, this);
    }

    getLast() {
        return this.getById(this.stack[this.stack.length-1]);
    }

    reset(){
        this.stack = [];
        this.data = {};
        this.initalStackData = {};
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
        case 'CARD_LEAVE':
            ColumnViewStore.leave(payload);
            break;
        case 'CARD_CLEAR_STACK':
            ColumnViewStore.clear(payload);
            break;
        case 'CARD_DROP':
            ColumnViewStore.drop(payload);
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
        case 'EXPLORER_RESET':
            ColumnViewStore.reset();
            break;
        case 'CARD_CHANGE_ATTRIBUTE':
            ColumnViewStore.updateAttribute(payload);
            break;
    }

    return true;
});



export default ColumnViewStore;
