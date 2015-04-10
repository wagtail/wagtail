var React = require("react/addons");
import scroll from 'scroll';
import Column from './Column';
import update from 'react/lib/update';
import ColumnViewActions from './actions/ColumnViewActions';

const CSSTransitionGroup = React.addons.CSSTransitionGroup;


// NeXT ColumnView

// Process:
// 1. Mount a node
// 2. Print the node's children.
// 3. On clicking a child node, mount that node as well
// 4. Display the new node's children.

const ColumnView = React.createClass({
    render() {
        const { data, stack } = this.props;

        const columns = stack.map((d, columnNumber) => {
            return (
                <Column
                    data={d}
                    stack={stack}
                    key={columnNumber}
                    index={columnNumber}
                />
            );
        }, this);

        return (
            <CSSTransitionGroup  component="div" className="bn-explorer__body" transitionName="column">
                {columns}
            </CSSTransitionGroup>
        );
    }
});

export default ColumnView;
