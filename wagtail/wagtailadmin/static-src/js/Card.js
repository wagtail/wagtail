import React, { PropTypes } from 'react';
import { DragDropMixin } from 'react-dnd';
import ItemTypes from './ItemTypes';


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
        const id = component.props.id;
        const column = component.props.column;
        component.props.moveCard(component.props.data, id, column, item);
    },
    leave(component, item) {
        // component.removePlaceholder();
    },
    acceptDrop(component, item, isHandled, effect) {
        const id = component.props.id;
        const column = component.props.column;
        component.props.updateCard(component.props.data, id, column, item)
    }
};



const Card = React.createClass({
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
            hasPlaceholder: false
        }
    },
    handleClick() {
        this.props.clickHandler();
        this.setState({
            active: true
        })
    },
    render() {
        const className = 'bn-node ' + (this.props.active ? "bn-node--active" : "");
        const { isDragging } = this.getDragState(ItemTypes.CARD);
        const { isHovering } = this.getDropState(ItemTypes.CARD);


        return (
            <div
                className={className}
                onClick={this.handleClick}
                style={{backgroundColor:  isHovering ? "red" : "" , opacity: isDragging ? ".25" : "1"}}
                {...this.dragSourceFor(ItemTypes.CARD)}
                {...this.dropTargetFor(ItemTypes.CARD)}
                >
                <h3>
                    {this.props.data.name}
                    {this.props.data.children || this.props.data.url ? <span className='icon bn-arrow'></span> : ""}
                </h3>
            </div>
        );
    }
});


export default Card;
