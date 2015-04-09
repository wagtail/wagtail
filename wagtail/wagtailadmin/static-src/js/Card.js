import React, { PropTypes } from 'react';
import { DragDropMixin } from 'react-dnd';
import ItemTypes from './ItemTypes';
import ColumnViewActions from './actions/ColumnViewActions';
import PageTypeStore from './stores/PageTypeStore';
import ColumnViewStore from './stores/ColumnViewStore';
import CardControls from './CardControls';


const ToolTip = React.createClass({
    render() {
        const {message} = this.props;
        return (
            <div className='bn-tooltip'>
                {message}
            </div>
        );
    }
});


const NodeStatusIndicator = React.createClass({
    render() {
        const { data } = this.props;
        const status = data.status;

        var className = "bn-status -" + status;

        return (
            <span className={className}>
            </span>
        );
    }
});



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
        const id        = component.props.id;
        const column    = component.props.column;
        ColumnViewActions.move(component.props.data, id, column, item)
    },
    leave(component, item) {
        const id        = component.props.id;
        const column    = component.props.column;
        ColumnViewActions.leave(component.props.data, id, column, item)
    },
    acceptDrop(component, item, isHandled, effect) {
        const id        = component.props.id;
        const column    = component.props.column;
        ColumnViewActions.move(component.props.data, id, column, item);
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
        const { data, id, column } = this.props;

        ColumnViewActions.show(data, id, column);

        if (data.children && !data.children.length && data.url) {
            ColumnViewActions.fetch({
                node: data,
                url: data.url
            });
        }
    },
    isSibling(node, stack) {
        var isSibling = false;

        if (stack.indexOf(node) > -1) {
            return isSibling;
        }

        // Array.some(). Who knew?
        isSibling = stack.some((item) => {
            return item.parent ? item.parent.children.indexOf(node) > -1 : false;
        });

        return isSibling;
    },
    isLast(node, stack) {
        return stack.indexOf(node) === stack.length-1;
    },
    render() {
        const { isDragging }        = this.getDragState(ItemTypes.CARD);
        const { isHovering }        = this.getDropState(ItemTypes.CARD);
        const { data, stack }       = this.props;
        const isLoading             = data.loading;

        var isSelected              = false;
        var isLast                  = false;
        var isSiblingOfSelected     = false;
        var className               = ['bn-node'];
        var type                    = PageTypeStore.getTypeByName(data.type);

        isSelected                  = stack.indexOf(data) > -1;
        isSiblingOfSelected         = this.isSibling(data, stack);
        isLast                      = this.isLast(data, stack);

        if (isSelected)             className.push('bn-node--active');
        if (isSiblingOfSelected)    className.push('bn-node--sibling');
        if (isHovering)             className.push('bn-node--hover');
        if (isDragging)             className.push('bn-node--drag');

        if (isLoading)              className.push('bn-node--loading');
        if (isLoading)              className.push('icon-spinner');

        if (!isLoading) {
            if (data.children.length) {
                className.push('bn-node--children');
            }
            if (data.url && !data.children.length) {
                className.push('bn-node--unloaded');
            }
        }

        return (
            <div className='bn-node-wrap'>
            <div
                className={className.join(" ")}
                onClick={this.handleClick}
                {...this.dragSourceFor(ItemTypes.CARD)}
                {...this.dropTargetFor(ItemTypes.CARD)} >
                <h3>
                    <NodeStatusIndicator data={data} />{data.name}
                </h3>
                <p>

                    {type ?
                        <span className="bn-node-type">
                            {type.verbose_name}
                        </span> : null }
                </p>
            </div>
            {isLast ? <CardControls data={data} stack={stack} /> : null}
            </div>
        );
    }
});


export default Card;
