import React from 'react';

import { StimulusWrapper } from '../../storybook/StimulusWrapper';
import { TabsController } from './TabsController';

export default {
  title: 'Stimulus / TabsController',
  argTypes: { debug: { control: 'boolean', defaultValue: false } },
};

const definitions = [
  { identifier: 'w-tabs', controllerConstructor: TabsController },
];

const Template = ({ debug = false }) => (
  <StimulusWrapper debug={debug} definitions={definitions}>
    <div data-controller="w-tabs" data-w-tabs-active-class="!w-translate-y-0">
      <div
        className="w-flex w-gap-4"
        role="tablist"
        data-action="keydown.right->w-tabs#selectNext keydown.left->w-tabs#selectPrevious keydown.home->w-tabs#selectFirst keydown.end->w-tabs#selectLast"
      >
        <a
          id="tab-1"
          href="#panel-1"
          role="tab"
          data-w-tabs-target="trigger"
          data-action="w-tabs#select:prevent"
        >
          Tab 1
        </a>
        <a
          id="tab-2"
          href="#panel-2"
          role="tab"
          aria-selected
          data-w-tabs-target="trigger"
          data-action="w-tabs#select:prevent"
        >
          Tab 2
        </a>
        <a
          id="tab-3"
          href="#panel-3"
          role="tab"
          data-w-tabs-target="trigger"
          data-action="w-tabs#select:prevent"
        >
          Tab 3
        </a>
      </div>
      <div className="w-border-solid w-border-2 w-mb-8 w-overflow-hidden">
        <section
          className="w-min-h-24 w-transition w-ease-in-out w-duration-200 w-translate-y-full w-bg-info-50"
          id="panel-1"
          role="tabpanel"
          aria-labelledby="tab-1"
          data-w-tabs-target="panel"
          data-action="w-focus:focus->w-tabs#selectInside"
        >
          Tab 1 content
        </section>
        <section
          className="w-min-h-24 w-transition w-ease-in-out w-duration-200 w-translate-y-full w-bg-positive-50"
          id="panel-2"
          role="tabpanel"
          aria-labelledby="tab-2"
          data-w-tabs-target="panel"
          data-action="w-focus:focus->w-tabs#selectInside"
        >
          Tab 2 content (selected by default)
        </section>
        <section
          className="w-min-h-24 w-transition w-ease-in-out w-duration-200 w-translate-y-full w-bg-grey-50"
          id="panel-3"
          role="tabpanel"
          aria-labelledby="tab-3"
          data-w-tabs-target="panel"
          data-action="w-focus:focus->w-tabs#selectInside"
        >
          Tab 3 content
        </section>
      </div>
      <button
        className="button"
        type="button"
        data-action="w-tabs#select"
        data-w-tabs-focus-param
        data-w-tabs-id-param="panel-1"
        data-w-tabs-target="trigger"
      >
        Trigger for Tab 1
      </button>
    </div>
  </StimulusWrapper>
);

export const Base = Template.bind({});
