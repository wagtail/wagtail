import React from 'react';
import 'babel/polyfill';
import scroll from 'scroll';

import PageService from './services/PageService';
import ColumnView from './ColumnView';
import ListView from './ListView';
import ColumnViewActions from './actions/ColumnViewActions';
import ColumnViewStore from './stores/ColumnViewStore';
import PageTypeActions from './actions/PageTypeActions';
import PageTypeStore from './stores/PageTypeStore';
import AppDispatcher from './dispatcher';
import Breadcrumb from './Breadcrumb';
import PageChooser from './PageChooser';


// Why is React awesome? One line debugger!
AppDispatcher.register( function( payload ) {
    console.log(payload);
});


const Explorer = React.createClass({
    getInitialState() {
        var pageService = new PageService();
        var data = pageService.fetch(this.handleFetch);
        var pageTypes = pageService.getPageTypes(this.handlePageTypes);

        return {
            currentView: "column",
            data: []
        }
    },
    componentDidMount() {
        ColumnViewStore.on( 'change', this.dataChanged );
        PageTypeStore.on( 'change', this.dataChanged );
    },
    componentWillUnmount() {
        ColumnViewStore.removeListener( 'change', this.dataChanged );
        PageTypeStore.removeListener( 'change', this.dataChanged );
    },
    handleFetch(data) {
        ColumnViewActions.populate(data);
    },
    handlePageTypes(payload) {
        PageTypeActions.populate(payload.data);
    },
    dataChanged() {
        var data = ColumnViewStore.getAll();
        this.setState({
            data: data
        });
    },
    handleRootNodeClick() {
        ColumnViewActions.clearStack();
    },
    render() {
        var view, el;

        const data = ColumnViewStore.getAll();
        const stack = ColumnViewStore.getStack();
        const pageTypes = PageTypeStore.getAll();
        const modal = ColumnViewStore.getModal();


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

        if (data.children) {
            el = React.createElement(view, {
                data,
                stack,
                pageTypes
            });
        } else {
            el = (
            <div className='bn-loading'>
                 <img src='/static/wagtailadmin/images/spinner.gif' />
            </div>);
        }

        return (
            <div className="bn-explorer-container">
                <div className="bn-explorer">
                    <div className="bn-explorer__header">
                        <h1>
                            <span
                                onClick={this.handleRootNodeClick}
                                className='bn-explorer__root'
                            >
                                Explorer
                            </span>
                            <small>
                                <Breadcrumb
                                    data={stack}
                                />
                            </small>

                        </h1>
                    </div>
                    <div className='bn-explorer__overflow'>
                        {el}
                    </div>
                    { modal ?
                    <div className='bn-modal' onClick={this.handleClose}>
                        <PageChooser
                            data={data}
                            stack={stack}
                            pageTypes={pageTypes}
                        />
                    </div> : null }
                </div>
            </div>
        );
    },
    handleClose() {
        ColumnViewActions.dismissModal();
    }
});



var originalClassName = "";

function handleInit(e) {
    var isReactified = false;
    var el = document.querySelector('.content-wrapper');
    var mount = document.createElement('div');

    function handleClick(e) {
        e.preventDefault();
        e.stopPropagation();

        if (!isReactified) {
            isReactified = true;
            ColumnViewActions.reset();

            var classes = document.body.className.split(" ");

            classes = classes.filter((item) => {
                var thing = item.match(/^menu/);

                if (thing) {
                    originalClassName = item;
                }
                return !thing;
            });

            classes.push('menu-explorer');

            document.body.className = classes.join(" ");
            React.render(React.createElement(Explorer), mount);
        } else {
            document.body.classList.remove('menu-explorer');
            document.body.classList.add(originalClassName);
            React.unmountComponentAtNode(mount);
            isReactified = false;
        }
    }


    var triggerEl = document.querySelector('[data-explorer-menu-url]');
    triggerEl.addEventListener('click', handleClick, false);

    el.appendChild(mount);
}



document.addEventListener('DOMContentLoaded', handleInit);

