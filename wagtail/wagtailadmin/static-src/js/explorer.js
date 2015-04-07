import React from 'react';
import 'babel/polyfill';
import scroll from 'scroll';

import PageService from './services/PageService';
import ColumnView from './ColumnView';
import ListView from './ListView';


const Explorer = React.createClass({
    getInitialState: function() {
        var pageService = new PageService();
        var data = pageService.fetch();

        return {
            currentView: "column",
            data: data
        }
    },
    render: function() {
        var view, el;

        switch (this.state.currentView) {
            case "column":
                view = ColumnView;
                break;
            case "list":
                view = ListView;
                break;
            default:
                view = ColumnView;
                break;
        }

        el = React.createElement(view, {
            data: this.state.data
        });

        return (
            <div>
                {el}
            </div>
        );
    }
});



document.addEventListener("DOMContentLoaded", function() {
    var el = document.querySelector('.content-wrapper');
    var mount = document.createElement("div");
    // var height = document.documentElement.offsetHeight;

    mount.classList.add("bn-explorer-container");
    // mount.style.height = height + "px";
    el.appendChild(mount);
    React.render(React.createElement(Explorer), mount);
});

