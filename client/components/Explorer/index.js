import React, { Component, PropTypes } from 'react';


export default class Explorer extends Component {

    constructor(props) {
        super(props);

        this.state = {};
    }

    componentDidMount() {

    }

    componentWillUnmount() {

    }

    render() {
        return (
            <div>

            </div>
        );
    }
}


Explorer.propTypes = {
    onPageSelect: PropTypes.func,
    initialPath: PropTypes.string,
    apiPath: PropTypes.string,
    size: PropTypes.number
};
