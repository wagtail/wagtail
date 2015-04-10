import React, { PropTypes } from 'react';
import ColumnViewActions from './actions/ColumnViewActions';
import PageTypeStore from './stores/PageTypeStore';


const CardControls = React.createClass({
    handleClick(e) {
        e.stopPropagation();
    },
    getInitialState: function() {
        return {
            confirmDelete: false
        }
    },
    handleRemove(e) {
        const { data, stack } = this.props;
        const { confirmDelete } = this.state;

        if (!confirmDelete) {
            this.setState({
                confirmDelete: true
            });

            return;
        }

        ColumnViewActions.removeCard(data.id);
    },
    cancelRemove(e) {
        this.setState({
            confirmDelete: false
        });
    },
    handleAdd(e) {
        ColumnViewActions.showModal();
    },
    render() {
        const { data, stack } = this.props;
        const typeInfo = PageTypeStore.getTypeByName(data.type);
        var supportsSubpages = typeInfo.subpage_types.length > 0;
        const { confirmDelete } = this.state;

        var deleteClassName = 'btn -tiny -none';

        if (confirmDelete) {
            deleteClassName += ' -danger';
        }

        return (
            <div
                className='bn-controls btn-group bn-reveal'
                onClick={this.handleClick}>
                <span className='btn -tiny -none' ><span className="icon icon-view" /></span>
                <span className='btn -tiny -none' >Edit</span>
                <span
                    className={deleteClassName}
                    onClick={this.handleRemove}>
                    { confirmDelete ? 'Confirm' : 'Delete' }
                </span>
                {confirmDelete ? <span onClick={this.cancelRemove} className='btn -tiny -positive'>×</span> : null}
                {supportsSubpages ?
                <span className='btn -tiny -none' onClick={this.handleAdd}>
                    Add
                </span> : null }
            </div>
        );
    }
});

export default CardControls;
