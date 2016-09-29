import React from 'react';


export default class PageChooserHeader extends React.Component {
  render() {
    return <header className="nice-padding hasform">
      <div className="row">
        <div className="left">
          <div className="col">
            <h1 className="icon icon-doc-empty-inverse">Choose a page</h1>
          </div>
          <form className="col search-form" noValidate="">
            <ul className="fields">
              <li className="required">
                <div className="field char_field text_input field-small iconfield">
                  <label htmlFor="id_q">Search term:</label>
                  <div className="field-content">
                    <div className="input icon-search ">
                      <input onChange={e => this.props.onSearch(e.target.value)} placeholder="Search" type="text" disabled={!this.props.searchEnabled} />
                      <span></span>
                    </div>
                  </div>
                </div>
              </li>
              <li className="submit visuallyhidden"><input value="Search" className="button" type="submit" /></li>
            </ul>
          </form>
        </div>
        <div className="right"></div>
      </div>
    </header>;
  }
}
