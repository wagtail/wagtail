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

/**
 * Example of the `enable` target usage within the RulesController.
 */
const EnableTemplate = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <form
      method="get"
      data-controller="w-rules"
      // avoid accidental submissions with preventing submit
      data-action="change->w-rules#resolve submit->w-rules#resolve:prevent"
    >
      <fieldset>
        <legend>
          An example of <strong>enabling</strong> secondary fields based on the
          primary fields having a value entered. Add a value to the email field
          to disable the link label or add a value to the link field to disable
          the email subject.
        </legend>
        <div className="w-field__wrapper">
          <label className="w-field__label" htmlFor="link-field">
            Enter a link:
          </label>
          <div className="w-field">
            <div className="w-field__input">
              <input type="url" name="link" id="link-field" />
            </div>
          </div>
        </div>
        <div className="w-field__wrapper">
          <label className="w-field__label" htmlFor="email-field">
            <strong>Or</strong> enter an Email address:
          </label>
          <div className="w-field">
            <div className="w-field__input">
              <input type="email" name="email" id="email-field" />
            </div>
          </div>
        </div>
        <hr />
        <div className="w-field__wrapper">
          <label className="w-field__label" htmlFor="drink">
            Enter an email subject:
          </label>
          <div className="w-field">
            <div className="w-field__input">
              <input
                type="text"
                name="subject"
                className="w-field__wrapper"
                data-w-rules='{"link":""}'
                data-w-rules-target="enable"
              />
            </div>
          </div>
        </div>
        <div className="w-field__wrapper">
          <label className="w-field__label" htmlFor="subject-field">
            Enter a link label:
          </label>
          <div className="w-field">
            <div className="w-field__input">
              <input
                type="email"
                name="subject"
                id="subject-field"
                data-w-rules='{"email":""}'
                data-w-rules-target="enable"
              />
            </div>
          </div>
        </div>
      </fieldset>
      <div>
        <p>Enter either a link or an email address, not both.</p>
        {/* Additional example of using match values, only ONE field should be blank to submit. */}
        <button
          type="submit"
          data-w-rules-target="enable"
          data-w-rules={JSON.stringify({ link: '', email: '' })}
          data-w-rules-match="one"
        >
          Submit
        </button>
      </div>
    </form>
  </StimulusWrapper>
);

/**
 * Example of the `show` target usage within the RulesController.
 */
const ShowTemplate = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <form
      method="get"
      data-controller="w-rules"
      // avoid accidental submissions with preventing submit
      data-action="change->w-rules#resolve submit->w-rules#resolve:prevent"
    >
      <fieldset>
        <legend>
          An example of <strong>showing</strong> a second field based on the
          value of the first field.
        </legend>
        <div className="w-field__wrapper">
          <label className="w-field__label" htmlFor="drink">
            Choose your favorite drink:
          </label>
          <div className="w-field w-field--select">
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
        </div>
        <div
          className="w-field__wrapper"
          data-w-rules-target="show"
          data-w-rules='{"drink":"other"}'
        >
          <label className="w-field__label" htmlFor="other">
            Other
          </label>
          <div className="w-field w-field--select">
            <div className="w-field__input">
              <input type="text" name="other" />
            </div>
          </div>
        </div>
      </fieldset>
    </form>
  </StimulusWrapper>
);

export const Enable = EnableTemplate.bind({});

export const Show = ShowTemplate.bind({});
