import React, { PropTypes } from 'react';
import { DragDropMixin } from 'react-dnd';
import ItemTypes from './ItemTypes';
import Card from './Card';

import ColumnViewActions from './actions/ColumnViewActions';

import PageTypeStore from './stores/PageTypeStore';
import ColumnViewStore from './stores/ColumnViewStore';
import scroll from 'scroll';


const dragSource = {
    beginDrag(component) {
        return {
            item: {
                id: component.props.id,
                column: component.props.column
            }
        };
    }
};

const dropTarget = {
    over(component, item) {
        console.log("DRAG over");


        const id = component.props.id;
        const column = component.props.column;
        this.setState({
            active: true
        });
        ColumnViewActions.move(component.props.data, id, column, item);
    },
    leave(component, item) {
        console.log("DRAG leave");

        const id = component.props.id;
        const column = component.props.column;
        ColumnViewActions.leave(component.props.data, id, column, item);
        this.setState({
            active: false
        });
    },
    acceptDrop(component, item, isHandled, effect) {
        const id = component.props.id;
        const column = component.props.column;
        ColumnViewActions.move(component.props.data, id, column, item);
    }
};


const Column = React.createClass({
    mixins: [ DragDropMixin ],
    statics: {
        configureDragDrop(register) {
            register(ItemTypes.CARD, {
                dragSource,
                dropTarget
            });
        }
    },
    getInitialState() {
        return {
            hasPlaceholder: false,
            active: false,
            nodeCountChanged: false,
            nodeCount: 0
        }
    },
    handleClick() {
       ColumnViewActions.showModal();
    },
    mapNodes(data, columnNumber) {
        return data.children.map(function(item, index) {
            return (
                <Card
                    data={item}
                    key={index}
                    id={index}
                    stack={this.props.stack}
                    column={columnNumber}
                />
            );
        }, this);
    },
    componentDidMount() {
        const node      = this.getDOMNode();
        const scroller  = document.querySelector(".bn-explorer__overflow");
        const left      = node.offsetLeft;

        scroll.left(scroller, left, { duration: 700, ease: 'inOutQuint' });
    },
    componentDidUpdate() {
        const { data, index, stack } = this.props;
        const last = stack[stack.length-1];

        if (last.id === data.id) {
            const node      = this.getDOMNode();
            const scroller  = document.querySelector(".bn-explorer__overflow");
            const left      = node.offsetLeft;

            scroll.left(scroller, left, { duration: 700, ease: 'inOutQuint' });
        }
    },
    render() {
        const { isDragging } = this.getDragState(ItemTypes.CARD);
        const { isHovering } = this.getDropState(ItemTypes.CARD);

        const { data, index, stack } = this.props;
        const nodes     = data.children ? this.mapNodes(data, index) : [];
        const last      = stack[stack.length-1];

        var isCurrent = false;
        var className = 'bn-column';
        var type = {subpage_types: []};
        var acceptsChildren = false;

        if (last.id === data.id) {
            isCurrent = true;
            type                = PageTypeStore.getTypeByName(data.type);
            acceptsChildren     = type.subpage_types.length > 0;
        }

        if (this.state.active) {
            className += ' bn-column--active';
        }


        return (
            <div className={className}>
                <div className='bn-column-scroll'>
                    { nodes.length ? nodes :
                         acceptsChildren ?
                        <div className='bn-column-placeholder'>
                            <p>No pages have been created.</p>
                            <span
                                className='btn -primary'
                                onClick={this.handleClick}>Why not add one?</span>
                        </div> : null
                     }
                </div>
            </div>
        );
    }
});

export default Column;

