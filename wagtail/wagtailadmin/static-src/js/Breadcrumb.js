import React, { PropTypes } from 'react';
import ColumnViewActions from './actions/ColumnViewActions';


const Breadcrumb = React.createClass({
    render: function() {
        const { data, clickHandler } = this.props;

        if (!data) {
            return (<span />)
        }

        const breadcrumb = data.map((item, index) => {

            if (!item) {
                return <span key={index} />
            }

            return (
                <span
                    key={index}
                    className='bn-breadcrum-item'
                    onClick={this.clickHandler.bind(this, item.id, index)}>
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
    clickHandler: function(id, index) {
        ColumnViewActions.show(id);
    }
});



export default Breadcrumb;
