import React, { useCallback } from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { CleanController } from './CleanController';

export default {
  title: 'Stimulus / CleanController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: true,
    },
  },
};

const definitions = [
  {
    identifier: 'w-clean',
    controllerConstructor: CleanController,
  },
];

const Template = ({ debug = false }) => {
  const [sourceValues, setSourceValue] = React.useState({});
  return (
    <StimulusWrapper debug={debug} definitions={definitions}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
        }}
        ref={useCallback((node) => {
          node.addEventListener(
            'w-clean:applied',
            ({ target, detail: { sourceValue } }) => {
              setSourceValue((state) => ({
                ...state,
                [target.id]: sourceValue,
              }));
            },
          );
        }, [])}
      >
        <fieldset>
          <legend>
            Focus and then remove focus (blur) on fields to see changes, trim is
            enabled for all.
          </legend>
          <div className="w-m-4">
            <label htmlFor="slugify">
              <pre>slugify</pre>
              <input
                id="slugify-default"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#slugify"
                data-w-clean-trim-value
              />
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['slugify-default']}</pre>
              </output>
            </label>
          </div>
          <div className="w-m-4">
            <label htmlFor="slugify-unicode">
              <pre>slugify (allow unicode)</pre>
              <input
                id="slugify-unicode"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#slugify"
                data-w-clean-allow-unicode-value
                data-w-clean-trim-value
              />
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['slugify-unicode']}</pre>
              </output>
            </label>
          </div>
          <div className="w-m-4">
            <label htmlFor="urlify-default">
              <pre>urlify</pre>
              <input
                id="urlify-default"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#urlify"
                data-w-clean-trim-value
              />
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['urlify-default']}</pre>
              </output>
            </label>
          </div>
          <div className="w-m-4">
            <label htmlFor="urlify-locale-uk">
              <pre>urlify (with Ukrainian locale)</pre>
              <input
                id="urlify-locale-uk"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#urlify"
                data-w-clean-locale-value="uk-UK"
                data-w-clean-trim-value
              />
              <p>Try `Георгій`, should be `heorhii`, not `georgij`.</p>
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['urlify-locale-uk']}</pre>
              </output>
            </label>
          </div>
          <div className="w-m-4">
            <label htmlFor="urlify-unicode">
              <pre>urlify (allow unicode)</pre>
              <input
                id="urlify-unicode"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#urlify"
                data-w-clean-allow-unicode-value
                data-w-clean-trim-value
              />
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['urlify-unicode']}</pre>
              </output>
            </label>
          </div>
          <div className="w-m-4">
            <label htmlFor="format-basic">
              <pre>format (remove !, replace digits with #)</pre>
              <input
                id="format-basic"
                type="text"
                data-controller="w-clean"
                data-action="blur->w-clean#format"
                data-w-clean-allow-unicode-value
                data-w-clean-formatters-value={JSON.stringify([
                  /!/.source,
                  [/\d/.source, '#'],
                ])}
                data-w-clean-trim-value
              />
              <output className="w-inline-flex w-items-center">
                Source value: <pre>{sourceValues['format-basic']}</pre>
              </output>
            </label>
          </div>
        </fieldset>
      </form>
    </StimulusWrapper>
  );
};

export const Base = Template.bind({});
