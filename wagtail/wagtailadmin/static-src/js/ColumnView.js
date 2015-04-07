import React from 'react';
import scroll from 'scroll';
import Card from './Card';
import PageService from './services/PageService';
import update from 'react/lib/update';
import isParent from './utils/common';





// NeXT ColumnView

// Process:
// 1. Mount a node
// 2. Print the node's children.
// 3. On clicking a child node, mount that node as well
// 4. Display the new node's children.

const ColumnView = React.createClass({
    getInitialState: function() {
        return {
            stack: [this.props.data],
            cards: [this.props.data]
        }
    },
    moveCard: function(item, afterId, column, newItem) {
        // const { stack } = this.state;
        // const targetColumn = stack[column];
        // const originalItem = stack[newItem.column].children[newItem.id];

        // if (isParent(item, originalItem)) {
        //     // TODO: Fire a message if user attempts to drag node into child.
        //     return;
        // }


        // targetColumn.children.splice(afterId, 0, item);
        // stack[column] = targetColumn;

        // // Original item
        // this.setState({
        //     stack: stack
        // });


    },
    updateCard: function(targetItem, afterId, column, newItem) {
        const { stack } = this.state;
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
        this.setState({
            stack: stack
        });
    },
    mapNodes: function(data, columnNumber) {
        var stack = this.state.stack;

        return data.children.map(function(item, index) {
            var isActive = stack.indexOf(item) > -1;
            var handler = this.handleNodeClick.bind(this, item, index, columnNumber)

            return (
                <Card
                    data={item}
                    active={isActive}
                    key={index}
                    id={index}
                    column={columnNumber}
                    clickHandler={handler}
                    moveCard={this.moveCard}
                    updateCard={this.updateCard}
                />
            );
        }, this);
    },
    render: function() {
        const { stack } = this.state;

        var columns = stack.map(function(data, columnNumber) {
            var nodes = data.children ? this.mapNodes(data, columnNumber) : [];

            return (
                <div className='bn-column' key={columnNumber}>
                    <div className='bn-column-scroll'>
                        { nodes }
                    </div>
                </div>
            );
        }, this);

        var breadcrumb = stack.map(function(item, index) {
            var handler = this.handleNodeClick.bind(this, item, index, index)

            return (
                <span onClick={handler}>
                    {item.name === "root" ? "" : item.name}
                    <span  className="bn-arrow" />
                </span>
            )
        }, this);

        return (
            <div className="bn-explorer">
                <div className="bn-explorer__header">
                    <h1>
                        <span onClick={this.clearStack}>Explorer</span>
                        <small>{breadcrumb}</small>
                    </h1>
                </div>

                <div className="bn-explorer__overflow">
                    <div className="bn-explorer__body">
                        {columns}
                    </div>
                </div>
            </div>
        );
    },

    clearStack: function() {
        this.setState({
            stack: [this.props.data]
        });
    },

    componentDidUpdate: function() {
        var node = this.getDOMNode();
        var scroller = node.querySelector(".bn-explorer__overflow");
        var all = node.querySelectorAll('.bn-node');
        var last = all[all.length-1];
        var left = last.offsetLeft;
        scroll.left(scroller, left, { duration: 700, ease: 'inOutQuint' });
    },

    handleNodeClick: function(node, index, level) {
        var stack = this.state.stack;
        var indexOfNode = stack.indexOf(node);

        if (stack.length > level && indexOfNode < stack.length) {
            while (stack.length > level + 1) {
                stack.pop();
            }
        }

        // Only allow items to be pushed onto the stack once.
        if (indexOfNode < 0) {
            stack.push(node);

            if ( ! node.children && node.url) {
                var service = new PageService();
                node.children = service.fetch(node.url);
            }
        }

        this.setState({
            stack: stack
        });
    }
});

export default ColumnView;
