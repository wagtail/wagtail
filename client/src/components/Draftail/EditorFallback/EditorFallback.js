import PropTypes from 'prop-types';
import React, { PureComponent } from 'react';
import { convertFromRaw } from 'draft-js';

import { STRINGS } from '../../../config/wagtailConfig';

const MAX_EDITOR_RELOADS = 3;

class EditorFallback extends PureComponent {
  constructor(props) {
    super(props);

    const { field } = props;

    this.state = {
      error: null,
      info: null,
      reloads: 0,
      showContent: false,
      showError: false,
      initialContent: field.value,
    };

    this.renderError = this.renderError.bind(this);
    this.toggleContent = this.toggleContent.bind(this);
    this.toggleError = this.toggleError.bind(this);
    this.onReloadEditor = this.onReloadEditor.bind(this);
  }

  componentDidCatch(error, info) {
    const { field } = this.props;
    const { initialContent } = this.state;

    this.setState({ error, info });

    field.value = initialContent;
  }

  onReloadEditor() {
    const { reloads } = this.state;

    this.setState({
      error: null,
      info: null,
      reloads: reloads + 1,
      showContent: false,
      showError: false,
    });
  }

  toggleContent() {
    const { showContent } = this.state;
    this.setState({ showContent: !showContent });
  }

  toggleError() {
    const { showError } = this.state;
    this.setState({ showError: !showError });
  }

  renderError() {
    const { field } = this.props;
    const { error, info, reloads, showContent, showError } = this.state;
    const content =
      field.rawContentState &&
      convertFromRaw(field.rawContentState).getPlainText();

    return (
      <div className="Draftail-Editor">
        <div className="Draftail-Toolbar">
          {content && (
            <button
              type="button"
              className="Draftail-ToolbarButton"
              onClick={this.toggleContent}
            >
              {STRINGS.SHOW_LATEST_CONTENT}
            </button>
          )}

          <button
            type="button"
            className="Draftail-ToolbarButton"
            onClick={this.toggleError}
          >
            {STRINGS.SHOW_ERROR}
          </button>

          {/* At first we propose reloading the editor. If it still crashes, reload the whole page. */}
          {reloads < MAX_EDITOR_RELOADS ? (
            <button
              type="button"
              className="Draftail-ToolbarButton"
              onClick={this.onReloadEditor}
            >
              {STRINGS.RELOAD_EDITOR}
            </button>
          ) : (
            <button
              type="button"
              className="Draftail-ToolbarButton"
              onClick={() => window.location.reload(false)}
            >
              {STRINGS.RELOAD_PAGE}
            </button>
          )}
        </div>

        <div className="DraftEditor-root">
          <div className="public-DraftEditor-content">
            <div className="public-DraftEditorPlaceholder-inner">
              {STRINGS.EDITOR_CRASH}

              {showContent && (
                <textarea
                  className="EditorFallback__textarea"
                  value={content}
                  readOnly
                />
              )}

              {showError && (
                <pre className="help-block help-critical">
                  <code className="EditorFallback__error">
                    {`${error.name}: ${error.message}\n\n${error.stack}\n${info.componentStack}`}
                  </code>
                </pre>
              )}
            </div>
          </div>
        </div>
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
  field: PropTypes.object.isRequired,
};

export default EditorFallback;
