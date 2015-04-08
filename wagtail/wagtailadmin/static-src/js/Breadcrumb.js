import React, { PropTypes } from 'react';
import ColumnViewActions from './actions/ColumnViewActions';


const Breadcrumb = React.createClass({
    render: function() {
        const { data, clickHandler } = this.props;

        if (!data) {
            return (<span />)
        }

        const breadcrumb = data.map((item, index) => {
            return (
                <span
                    key={index}
                    className='bn-breadcrum-item'
                    onClick={this.clickHandler.bind(this, item, index)}>
                    {item.name === "root" ? "" : item.name}
                    <span  className="bn-arrow" />
                </span>
            )
        }, this);

        return (
            <span className='bn-breadcrumb'>
                {breadcrumb}
            </span>
        );
    },
    clickHandler: function(item, index) {
        ColumnViewActions.show(item, index, index);
    }
});



export default Breadcrumb;
