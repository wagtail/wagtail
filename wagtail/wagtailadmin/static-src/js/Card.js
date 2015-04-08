import React, { PropTypes } from 'react';
import { DragDropMixin } from 'react-dnd';
import ItemTypes from './ItemTypes';
import ColumnViewActions from './actions/ColumnViewActions';
import PageTypeStore from './stores/PageTypeStore';


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
        ColumnViewActions.move(component.props.data, id, column, item)
    },
    leave(component, item) {
        ColumnViewActions.leave(component.props.data, id, column, item)
    },
    acceptDrop(component, item, isHandled, effect) {
        const id = component.props.id;
        const column = component.props.column;
        ColumnViewActions.move(component.props.data, id, column, item);
    }
};


const CardControls = React.createClass({
    handleClick(e) {
        e.stopPropagation();
    },
    handleRemove(e) {
        const { data, stack } = this.props;
        ColumnViewActions.removeCard(data);
    },
    handleAdd(e) {
        ColumnViewActions.showModal();
    },
    render() {
        const { data, stack } = this.props;
        return (
            <div
                className='bn-controls btn-group bn-reveal'
                onClick={this.handleClick}>
                <span className='btn -small' >Edit</span>
                <span className='btn -small' >Move</span>
                <span
                    className='btn -small'
                    onClick={this.handleRemove}>
                    Delete
                </span>
                <span className='btn -small' onClick={this.handleAdd}>
                    Add page
                </span>
            </div>
        );
    }
});



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
        const { data, id, column } = this.props;

        ColumnViewActions.show(data, id, column);

        if (data.children && !data.children.length && data.url) {
            ColumnViewActions.fetch({
                node: data,
                url: data.url
            });
        }
    },
    render() {
        const { isDragging } = this.getDragState(ItemTypes.CARD);
        const { isHovering } = this.getDropState(ItemTypes.CARD);
        const { data, stack } = this.props;
        const isLoading = data.loading;
        var isSelected = false;
        var isLast = false;


        var type = PageTypeStore.getTypeByName(data.type);

        if (stack.indexOf(data) > -1) {
            isSelected = true;
        }

        if (stack.indexOf(data) === stack.length-1) {
            isLast = true;
        }

        var canAddChildPage = isLast;
        var className = 'bn-node ' + (isSelected ? 'bn-node--active': '');

        return (
            <div
                className={className}
                onClick={this.handleClick}
                style={{backgroundColor:  isHovering ? "red" : "" , opacity: isDragging ? ".25" : null}}
                {...this.dragSourceFor(ItemTypes.CARD)}
                {...this.dropTargetFor(ItemTypes.CARD)}
            >
                <h3>
                    {data.name}
                    {isLoading ? <img src='/static/wagtailadmin/images/spinner.gif' width="16" height="16" /> : null }
                    {!isLoading && data.children && data.children.length ? <span className='icon bn-arrow'></span> : null}
                    {!isLoading && data.url && !data.children.length ? <span className='icon bn-arrow bn-arrow-unloaded'></span> : null}
                </h3>
                <p>
                    {data.status} | {type ? type.verbose_name : null }
                </p>
                {isLast ? <CardControls data={data} stack={stack} /> : null}
            </div>
        );
    }
});


export default Card;
