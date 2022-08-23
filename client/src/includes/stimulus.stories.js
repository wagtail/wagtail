/* eslint-disable max-classes-per-file */

/**
 * Example Stimulus usage within Storybook, including StimulusWrapper export
 * Note: Must use .js not .tsx for now
 */

import React from 'react';
import PropTypes from 'prop-types';
import { Controller } from '@hotwired/stimulus';
import { initStimulus } from './stimulus';

/**
 * Wrapper around the Stimulus application to ensure that the application
 * is scoped to only the specific story instance's DOM and also ensure
 * that the hot-reloader / page switches to not re-instate new applications
 * each time.
 *
 * @example
 * import Stories from '../includes/stimulus.stories';
 * const Template = () => <Stories.StimulusWrapper controllers={{ 'w-auto-form': AutoFormController }}><form data-controller="w-auto-form" /></Stories.StimulusWrapper>
 */
class StimulusWrapper extends React.Component {
  constructor(props) {
    super(props);
    this.ref = React.createRef();
  }

  componentDidMount() {
    const { controllers = [], debug = false } = this.props;

    // convert convenience object into identifier / controllerConstructor array if needed
    const definitions = Array.isArray(controllers)
      ? controllers
      : Object.entries(controllers).map(
          ([identifier, controllerConstructor]) => ({
            identifier,
            controllerConstructor,
          }),
        );

    this.application = initStimulus({
      debug,
      definitions,
      element: this.ref.current,
    });
  }

  componentDidUpdate({ debug: prevDebug }) {
    const { debug } = this.props;
    if (debug !== prevDebug) {
      this.application.debug = debug;
    }
  }

  componentWillUnmount() {
    this.application.stop();
    delete this.application;
  }

  render() {
    const { children } = this.props;
    return <section ref={this.ref}>{children}</section>;
  }
}

StimulusWrapper.propTypes = {
  /** Use the convenience controller object syntax {'my-identifier': MyController}
   * or verbose array syntax [{ identifier: 'my-identifier', controllerConstructor: My Controller}]
   */
  controllers: PropTypes.oneOfType([
    PropTypes.objectOf(PropTypes.func),
    PropTypes.arrayOf(
      PropTypes.shape({
        controllerConstructor: PropTypes.func,
        identifier: PropTypes.string,
      }),
    ),
  ]),
  /** Enable debug mode for verbose logging in the console */
  debug: PropTypes.bool,
};

StimulusWrapper.defaultProps = {
  controllers: [],
  debug: false,
};

/**
 * An example Stimulus controller that allows for an element to have
 * a random dice value.
 */
class ExampleDiceController extends Controller {
  static targets = ['element'];
  static values = { number: { type: Number, default: 6 } };

  connect() {
    this.roll();
  }

  roll() {
    // eslint-disable-next-line prefer-destructuring
    const numberValue = this.numberValue;
    const element = this.elementTarget;

    const result = Math.floor(Math.random() * numberValue) + 1;

    if (numberValue === 6) {
      element.setAttribute('title', `${result}`);
      element.textContent = `${['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'][result - 1]}`;
      return;
    }

    element.removeAttribute('title');
    element.textContent = `${result}`;
  }
}

const Template = ({ debug, number }) => (
  <StimulusWrapper controllers={{ dice: ExampleDiceController }} debug={debug}>
    <p
      data-controller="dice"
      {...(number && { 'data-dice-number-value': number })}
    >
      <button type="button" className="button w-mr-3" data-action="dice#roll">
        Roll the dice
      </button>
      <kbd
        data-dice-target="element"
        style={{
          display: 'inline-block',
          minWidth: '4ch',
          textAlign: 'center',
        }}
      />
    </p>
  </StimulusWrapper>
);

export default {
  title: 'Stimulus/Example',
  argTypes: {
    debug: {
      control: { type: 'boolean' },
      defaultValue: true,
    },
    number: {
      control: { type: 'select' },
      description: 'Dice sides',
      options: [2, 4, 6, 10, 20],
    },
  },
  StimulusWrapper, // available for other stories to import
};

export const Base = Template.bind({ debug: true });
