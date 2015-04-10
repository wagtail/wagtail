import React, { PropTypes } from 'react';

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

export default NodeStatusIndicator;
