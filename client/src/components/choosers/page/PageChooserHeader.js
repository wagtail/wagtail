import React from 'react';
import PropTypes from 'prop-types';

const propTypes = {
  onSearch: PropTypes.func.isRequired,
  searchEnabled: PropTypes.bool.isRequired,
};

const PageChooserHeader = ({ onSearch, searchEnabled }) => (
  <header className="nice-padding hasform">
    <div className="row">
      <div className="left">
        <div className="col">
          <h1 className="icon icon-doc-empty-inverse">
            Choose a page
          </h1>
        </div>
        <form className="col search-form" noValidate={true}>
          <ul className="fields">
            <li className="required">
              <div className="field char_field text_input field-small iconfield">
                <label htmlFor="id_q">
                  Search term:
                </label>
                <div className="field-content">
                  <div className="input icon-search ">
                    <input
                      onChange={e => onSearch(e.target.value)}
                      placeholder="Search"
                      type="text"
                      disabled={!searchEnabled}
                    />
                    <span />
                  </div>
                </div>
              </div>
            </li>
            <li className="submit visuallyhidden">
              <input value="Search" className="button" type="submit" />
            </li>
          </ul>
        </form>
      </div>
      <div className="right" />
    </div>
  </header>
);

PageChooserHeader.propTypes = propTypes;

export default PageChooserHeader;
