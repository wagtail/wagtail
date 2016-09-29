import React from 'react';


export class ModalWindow extends React.Component {
  renderModalContents () {
    return <div>Empty</div>;
  }

  render() {
    return (
      <div>
        <div className="modal fade in" tabIndex="-1" role="dialog" aria-hidden="true" style={{display: "block"}}>
          <div className="modal-dialog">
            <div className="modal-content">
              <button onClick={this.props.onModalClose} type="button" className="button close icon text-replace icon-cross" data-dismiss="modal" aria-hidden="true">&times;</button>
              <div className="modal-body">{this.renderModalContents()}</div>
            </div>
          </div>
        </div>
        <div className="modal-backdrop fade in"></div>
      </div>
    );
  }
}
