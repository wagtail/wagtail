import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { DrilldownController } from './DrilldownController';

export default {
  title: 'Stimulus / DrilldownController',
  argTypes: {
    debug: {
      control: 'boolean',
      defaultValue: false,
    },
  },
};

const definitions = [
  { identifier: 'w-drilldown', controllerConstructor: DrilldownController },
];

const sections = [
  { label: 'Section 1', key: 0 },
  { label: 'Section 2', key: 1 },
  { label: 'Section 3', key: 2 },
];

const Template = ({ debug }) => (
  <StimulusWrapper definitions={definitions} debug={debug}>
    <section>
      <div
        id="filters-drilldown"
        className="w-drilldown"
        data-controller="w-drilldown"
        data-w-drilldown-count-attr-value="data-w-active-filter-id"
      >
        <div className="w-drilldown__menu" data-w-drilldown-target="menu">
          <h2>Show</h2>
          {sections.map(({ label, key }) => (
            <button
              className="w-drilldown__toggle"
              key={key}
              type="button"
              aria-expanded="false"
              aria-controls={`drilldown-field-${key}`}
              data-w-drilldown-target="toggle"
              data-action="click->w-drilldown#open"
            >
              {label}
            </button>
          ))}
        </div>
        {sections.map(({ label, key }) => (
          <div
            className="w-drilldown__submenu w-flex w-flex-col"
            key={key}
            id={`drilldown-field-${key}`}
            hidden
            tabIndex="-1"
          >
            <span>{label} contents</span>
            <button
              className="w-drilldown__back"
              type="button"
              data-action="click->w-drilldown#close"
            >
              Back
            </button>
          </div>
        ))}
      </div>
    </section>
  </StimulusWrapper>
);

export const Base = Template.bind({});
