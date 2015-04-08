import React from 'react';
import scroll from 'scroll';
import Column from './Column';
import update from 'react/lib/update';
import ColumnViewActions from './actions/ColumnViewActions';



// NeXT ColumnView

// Process:
// 1. Mount a node
// 2. Print the node's children.
// 3. On clicking a child node, mount that node as well
// 4. Display the new node's children.

const ColumnView = React.createClass({
    componentDidUpdate() {
        // const node = this.getDOMNode();
        // const scroller = node.querySelector(".bn-explorer__overflow");
        // const all = node.querySelectorAll('.bn-node');
        // const last = all[all.length-1];
        // const left = last.offsetLeft;
        // scroll.left(scroller, left, { duration: 700, ease: 'inOutQuint' });
    },
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
            <div className="bn-explorer__body">
                {columns}
            </div>
        );
    }
});

export default ColumnView;
