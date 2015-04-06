var React = require("react");
var PageService = require("./services/PageService");
var scroll = require('scroll');

var Node = React.createClass({
    render: function() {
        var className = 'bn-node ' + (this.props.active ? "bn-node--active" : "");

        return (
            <div className={className}  onClick={this.handleClick}>
                <h3>
                    {this.props.data.name}
                    {this.props.data.children ? <span className='icon bn-arrow'></span> : ""}
                </h3>
            </div>
        );
    },
    handleClick: function() {
        this.props.clickHandler();
        this.setState({
            active: true
        })
    }
});


// NeXT ColumnView

// Process:
// 1. Mount a node
// 2. Print the node's children.
// 3. On clicking a child node, mount that node as well
// 4. Display the new node's children.

var ColumnView = React.createClass({
    getInitialState: function() {
        var pageService = new PageService();
        var data = pageService.fetch();

        return {
            data: data,
            stack: [data]
        }
    },
    render: function() {
        var data = this.state.data;
        var stack = this.state.stack;


        var columns = stack.map(function(data, columnNumber) {

            // Always print the children of a node.

            var nodes = data.children ? data.children.map(function(item, index) {
                var isActive = stack.indexOf(item) > -1;

                return (
                    <Node
                        data={item}
                        active={isActive}
                        key={index}
                        level={columnNumber}
                        clickHandler={this.handleNodeClick.bind(this, item, index, columnNumber)}
                    />
                );
            }, this) : [];

            return (
                <div className='bn-column' key={columnNumber}>
                    <div className='bn-column-scroll'>
                        { nodes }
                    </div>
                </div>
            );
        }, this);

        var breadcrumb = stack.map(function(item, index) {
            return (
                <span>
                    {item.name === "root" ? "" : item.name}
                    <span className="bn-arrow" />
                </span>
            )
        });

        return (
            <div className="bn-explorer" data={data}>
                <div className="bn-explorer__header">
                    <h1>
                        Explorer
                        <small>{breadcrumb}</small>
                    </h1>
                </div>

                <div className="bn-explorer__overflow">
                    <div className="bn-explorer__body">
                        {columns}
                    </div>
                </div>
            </div>
        );
    },

    componentDidUpdate: function() {
        var node = this.getDOMNode();
        var scroller = node.querySelector(".bn-explorer__overflow");
        var all = node.querySelectorAll('.bn-node');
        var last = all[all.length-1];
        var left = last.offsetLeft;
        scroll.left(scroller, left, { duration: 700, ease: 'inOutQuint' });
    },

    handleNodeClick: function(node, index, level) {
        var stack = this.state.stack;
        var indexOfNode = stack.indexOf(node);

        if (stack.length > level && indexOfNode < stack.length) {
            while (stack.length > level + 1) {
                stack.pop();
            }
        }

        // Only allow items to be pushed onto the stack once.
        if (indexOfNode < 0) {
            stack.push(node);

            if ( ! node.children && node.url) {
                var service = new PageService();
                node.children = service.fetch(node.url);
            }
        }

        this.setState({
            stack: stack
        });
    }
});


document.addEventListener("DOMContentLoaded", function() {
    var el = document.querySelector('.content-wrapper');
    var mount = document.createElement("div");
    var height = document.documentElement.offsetHeight;

    mount.classList.add("bn-explorer-container");
    mount.style.height = height + "px";
    el.appendChild(mount);
    React.render(React.createElement(ColumnView), mount);
});

