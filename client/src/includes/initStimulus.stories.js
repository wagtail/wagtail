import React from 'react';

import { Controller } from '@hotwired/stimulus';
import { StimulusWrapper } from '../../storybook/StimulusWrapper';

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

const definitions = [
  { controllerConstructor: ExampleDiceController, identifier: 'dice' },
];

const Template = ({ debug, number }) => (
  <StimulusWrapper
    debug={debug}
    definitions={[
      { controllerConstructor: ExampleDiceController, identifier: 'dice' },
    ]}
  >
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
};

export const Base = Template.bind({ debug: true });
