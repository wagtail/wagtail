import React, { PropTypes } from 'react';
import { DragDropMixin } from 'react-dnd';
import ItemTypes from './ItemTypes';
import Card from './Card';

import ColumnViewActions from './actions/ColumnViewActions';


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
            active: false
        }
    },
    handleClick() {
        // this.props.clickHandler();
        // this.setState({
        //     active: true
        // })
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
    render() {
        const { isDragging } = this.getDragState(ItemTypes.CARD);
        const { isHovering } = this.getDropState(ItemTypes.CARD);

        const { data, index, stack } = this.props;
        const nodes = data.children ? this.mapNodes(data, index) : [];

        var isCurrent = false;

        if (stack[stack.length-1] === data) {
            isCurrent = true;
        }

        var className = 'bn-column';

        if (this.state.active) className += ' bn-column--active';

        return (
            <div className={className}>
                <div className='bn-column-scroll'>
                    { nodes.length ? nodes : "" }
                </div>
            </div>
        );
    }
});

export default Column;

// { data.children && !nodes.length && isCurrent ? <AddButton data={data} /> : null }
// column={columnNumber}
// clickHandler={clickHandler}
// moveHandler={moveHandler}
// updateHandler={updateHandler}
