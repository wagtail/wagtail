import type { Application, Definition } from '@hotwired/stimulus';
import React from 'react';
import { initStimulus } from '../src/includes/initStimulus';

/**
 * Wrapper around the Stimulus application to ensure that the application
 * is scoped to only the specific story instance's DOM and also ensure
 * that the hot-reloader / page switches to not re-instate new applications
 * each time.
 *
 * @example
 * import { StimulusWrapper } from '../storybook/StimulusWrapper';
 * const Template = ({ debug }) =>
 *   <StimulusWrapper
 *     definitions={[{ controllerConstructor: SubmitController, identifier: 'w-something' }]}
 *     debug={debug}
 *   >
 *     <form data-controller="w-something" />
 *   </StimulusWrapper>
 */
export class StimulusWrapper extends React.Component<{
  debug?: boolean;
  definitions?: Definition[];
}> {
  ref: React.RefObject<HTMLDivElement>;
  application?: Application;

  constructor(props) {
    super(props);
    this.ref = React.createRef();
  }

  componentDidMount() {
    const { debug = false, definitions = [] } = this.props;
    const root = this.ref.current || document.documentElement;
    this.application = initStimulus({ debug, definitions, root });
  }

  componentDidUpdate({ debug: prevDebug }) {
    const { debug } = this.props;
    if (debug !== prevDebug) {
      Object.assign(this.application as Application, { debug });
    }
  }

  componentWillUnmount() {
    if (!this.application) return;
    this.application.stop();
    delete this.application;
  }

  render() {
    const { children } = this.props;
    return <div ref={this.ref}>{children}</div>;
  }
}
