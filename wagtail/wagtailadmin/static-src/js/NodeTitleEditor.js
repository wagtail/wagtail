import React, { PropTypes } from 'react';
import ColumnViewActions from './actions/ColumnViewActions';
import ColumnViewStore from './stores/ColumnViewStore';


const NodeTitleEditor = React.createClass({
    getInitialState() {
        return {
            edit:   false,
            value:  ''
        }
    },
    toggleEdit(e) {
        e.stopPropagation();

        const { data }  = this.props;
        const edit      = data.edit ? data.edit : false;

        ColumnViewActions.updateAttribute({
            node:           data,
            attribute:      'edit',
            value:          true
        });

        this.setState({
            value: data.name
        });
    },
    save(e) {
        e.stopPropagation();

        if (!this.state.value) {
            return;
        }

        if (this.state.value !== this.props.data.name) {
            ColumnViewActions.updateAttribute({
                node:           this.props.data,
                attribute:      'name',
                value:          this.state.value
            });

            ColumnViewActions.updateAttribute({
                node:           this.props.data,
                attribute:      'edit',
                value:          false
            });
        }

        this.setState({
            edit:   false,
            value:  ''
        });
    },
    handleChange(e) {
        const value = e.target.value;
        this.setState({
            value: value
        });
    },
    cancelEdit(e) {
        e.stopPropagation();
        console.log('cancel');

        ColumnViewActions.updateAttribute({
            node:           this.props.data,
            attribute:      'edit',
            value:          false
        });
    },
    render() {
        const { data }      = this.props;
        const canEdit       = data.edit;
        const last          = ColumnViewStore.getLast();
        var child           = data.name;

        if (canEdit) {
            child = (
                <input
                    type='text'
                    className='bn-title-edit'
                    defaultValue={data.name}
                    onChange={this.handleChange} />
            );
        }

        var handler = last === data ? this.toggleEdit : null;

        return (
            <span className="" onClick={handler}>
                {child}
                {canEdit ?
                    <span className='btn-group'>
                        <span className='btn' onClick={this.save}>Save</span>
                        <span className='btn' onClick={this.cancelEdit}>Cancel</span>
                    </span>
                : null  }
            </span>
        );
    }
});


export default NodeTitleEditor;
