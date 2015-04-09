import React, { PropTypes } from 'react';
import ColumnViewActions from './actions/ColumnViewActions';
import PageTypeStore from './stores/PageTypeStore';


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
        const typeInfo = PageTypeStore.getTypeByName(data.type);
        var supportsSubpages = typeInfo.subpage_types.length > 0;

        return (
            <div
                className='bn-controls btn-group bn-reveal'
                onClick={this.handleClick}>
                <span className='btn -tiny -none' ><span className="icon icon-view" /></span>
                <span className='btn -tiny -none' >Edit</span>
                <span
                    className='btn -tiny -none'
                    onClick={this.handleRemove}>
                    Delete
                </span>
                {supportsSubpages ?
                <span className='btn -tiny -none' onClick={this.handleAdd}>
                    Add
                </span> : null }
            </div>
        );
    }
});

export default CardControls;
