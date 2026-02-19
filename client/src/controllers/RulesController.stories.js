import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { RulesController } from './RulesController';

export default {
  title: 'Stimulus / RulesController',
  argTypes: {
    debug: { control: 'boolean', defaultValue: false },
  },
};

const definitions = [
  { identifier: 'w-rules', controllerConstructor: RulesController },
];

const EnableTemplate = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <form
      method="get"
      data-controller="w-rules"
      // avoid accidental submissions with preventing submit
      data-action="change->w-rules#resolve submit->w-rules#resolve:prevent"
    >
      <div className="w-field__wrapper">
        <label id="link-label" className="w-field__label" htmlFor="link-field">
          Enter a link:
        </label>
        <div className="w-field">
          <div className="w-field__input">
            <input
              type="url"
              name="link"
              id="link-field"
              aria-labelledby="link-label"
            />
          </div>
        </div>
      </div>
      <div className="w-field__wrapper">
        <label
          id="email-label"
          className="w-field__label"
          htmlFor="email-field"
        >
          Or enter an Email address:
        </label>
        <div className="w-field">
          <div className="w-field__input">
            <input
              type="email"
              name="email"
              id="email-field"
              aria-labelledby="email-label"
            />
          </div>
        </div>
      </div>
      <hr />
      <div>
        <label
          id="email-subject-label"
          className="w-field__label"
          htmlFor="email-subject"
        >
          Enter an email subject:
        </label>
        <div className="w-field">
          <div className="w-field__input">
            <input
              type="text"
              name="subject"
              id="email-subject"
              aria-labelledby="email-subject-label"
              className="w-field__wrapper"
              data-w-rules='{"link":""}'
              data-w-rules-target="enable"
            />
          </div>
        </div>
      </div>
      <div className="w-field__wrapper">
        <label
          id="subject-label"
          className="w-field__label"
          htmlFor="subject-field"
        >
          Enter a link label:
        </label>
        <div className="w-field">
          <div className="w-field__input">
            <input
              type="email"
              name="subject"
              id="subject-field"
              aria-labelledby="subject-label"
              data-w-rules='{"email":""}'
              data-w-rules-target="enable"
            />
          </div>
        </div>
      </div>
    </form>
  </StimulusWrapper>
);

const ShowTemplate = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <form
      method="get"
      data-controller="w-rules"
      // avoid accidental submissions with preventing submit
      data-action="change->w-rules#resolve submit->w-rules#resolve:prevent"
    >
      <div className="w-field__wrapper">
        <label className="w-field__label" htmlFor="drink">
          Choose your favorite drink:
          <div className="w-field w-field--choice_field w-field--select">
            <div className="w-field__input">
              <select className="w-min-w-full" name="drink">
                <option value="">-------</option>
                <option value="coffee">Coffee ☕</option>
                <option value="tea">Tea 🍵</option>
                <option value="milo">Milo 🍫</option>
                <option value="other">Other ❓</option>
              </select>
            </div>
          </div>
        </label>
      </div>
      <div
        className="w-field__wrapper"
        data-w-rules-target="show"
        data-w-rules='{"drink":"other"}'
      >
        <label id="other-label" className="w-field__label" htmlFor="other">
          Other
        </label>
        <div className="w-field w-field--choice_field w-field--select">
          <div className="w-field__input">
            <input
              type="text"
              name="other"
              id="other"
              aria-labelledby="other-label"
            />
          </div>
        </div>
      </div>
    </form>
  </StimulusWrapper>
);

export const Enable = EnableTemplate.bind({});

export const Show = ShowTemplate.bind({});
