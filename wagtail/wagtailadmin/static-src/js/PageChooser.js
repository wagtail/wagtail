import React from 'react';
import ColumnViewActions from './actions/ColumnViewActions';


const PageChooser = React.createClass({
    render() {
        const { stack, data, pageTypes } = this.props;

        var last = stack[stack.length-1];

        var typeDef = pageTypes.find((item) => {
            return item.type === last.type;
        })

        if (!typeDef || !typeDef.subpage_types) {
            return <div />
        }

        var validTypes = typeDef.subpage_types;
        console.log(last, typeDef);

        var typeDefs = validTypes.map((typeName, index) => {
            return pageTypes.find((n) => {
                return n.type === typeName;
            });
        }).filter((i) => { return !!i; });

        console.log(typeDefs);


        var typeOptions = typeDefs.map((typeObject, index) => {

            return (
                <p
                    className='btn bn-choser-item'
                    key={index}
                    onClick={this.handleAdd.bind(this, last, typeObject, index)}
                >
                    <span className="icon icon-doc-full" style={{fontSize: '2em'}}></span>
                    <br />
                    {typeObject.verbose_name}
                </p>
            );
        }, this);

        const name = last.name;

        return (
            <div className="bn-modal-view bn-chooser" onClick={this.handleClick}>
                <h2>Add something to '{name}':</h2>
                <hr />
                {typeOptions}
            </div>
        )
    },
    handleAdd(target, typeObject, index) {
        ColumnViewActions.createCard({
            target: target.id,
            typeObject,
            index
        });

        ColumnViewActions.dismissModal();
    },
    handleClick(e) {
        // Prevent the modal from closing when you click on it.
        e.stopPropagation();
    }
});

export default PageChooser;
