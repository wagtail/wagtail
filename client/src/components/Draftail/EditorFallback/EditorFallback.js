import PropTypes from 'prop-types';
import React, { PureComponent } from 'react';
import { convertFromRaw } from 'draft-js';

import { STRINGS } from '../../../config/wagtailConfig';

class EditorFallback extends PureComponent {
  constructor(props) {
    super(props);

    const { field } = props;

    this.state = {
      error: null,
      isContentShown: false,
      initialContent: field.value,
    };

    this.renderError = this.renderError.bind(this);
    this.toggleContent = this.toggleContent.bind(this);
  }

  componentDidCatch(error) {
    const { field } = this.props;
    const { initialContent } = this.state;

    this.setState({ error });

    field.value = initialContent;
  }

  toggleContent() {
    const { isContentShown } = this.state;
    this.setState({ isContentShown: !isContentShown });
  }

  renderError() {
    const { field } = this.props;
    const { isContentShown } = this.state;
    const content = field.rawContentState && convertFromRaw(field.rawContentState).getPlainText();

    return (
      <div className="Draftail-Editor">
        <div className="Draftail-Toolbar">
          <button
            type="button"
            className="Draftail-ToolbarButton"
            onClick={() => window.location.reload(false)}
          >
            {STRINGS.RELOAD_PAGE}
          </button>
          {content && (
            <button
              type="button"
              className="Draftail-ToolbarButton"
              onClick={this.toggleContent}
            >
              {STRINGS.SHOW_LATEST_CONTENT}
            </button>
          )}
        </div>
        <div className="DraftEditor-root">
          <div className="public-DraftEditorPlaceholder-inner">
            {STRINGS.EDITOR_CRASH}
          </div>
        </div>
        {isContentShown && (
          <textarea className="EditorFallback__textarea" value={content} readOnly />
        )}
      </div>
    );
  }

  render() {
    const { children } = this.props;
    const { error } = this.state;

    return error ? this.renderError() : children;
  }
}

EditorFallback.propTypes = {
  children: PropTypes.node.isRequired,
};

export default EditorFallback;
