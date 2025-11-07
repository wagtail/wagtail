import React from 'react';

export default {
  title: 'Shared / Scroll To Top Button',
  parameters: {
    docs: {
      description: {
        component:
          'A floating button that appears when the user scrolls down the page and smoothly scrolls back to the top when clicked. Improves navigation on pages with lengthy content.',
      },
    },
  },
};

const Template = () => (
  <div>
    <div style={{ height: '200vh', padding: '2rem' }}>
      <h1>Scroll down to see the button appear</h1>
      <p>The scroll-to-top button will appear after scrolling past 300px.</p>
      <p>
        Try scrolling down, and you&apos;ll see a floating button in the
        bottom-right corner.
      </p>
      <p>Click the button to smoothly scroll back to the top.</p>

      <div style={{ marginTop: '50vh' }}>
        <h2>Keep scrolling...</h2>
        <p>The button should now be visible if you&apos;re on this section.</p>
      </div>

      <div style={{ marginTop: '50vh' }}>
        <h2>Almost there...</h2>
        <p>Click the button to go back to the top!</p>
      </div>
    </div>

    <button
      type="button"
      className="w-scroll-top-button"
      data-controller="w-scroll-top"
      data-w-scroll-top-threshold-value="300"
      data-action="click->w-scroll-top#scrollToTop"
      aria-label="Scroll to top"
      hidden
    >
      <svg className="w-scroll-top-icon" aria-hidden="true">
        <use href="#icon-arrow-up" />
      </svg>
    </button>
  </div>
);

export const Default = Template.bind({});
Default.parameters = {
  docs: {
    description: {
      story:
        'The default scroll-to-top button appears after scrolling 300px down the page.',
    },
  },
};

const CustomThresholdTemplate = () => (
  <div>
    <div style={{ height: '200vh', padding: '2rem' }}>
      <h1>Custom Threshold (100px)</h1>
      <p>This button will appear after scrolling just 100px.</p>
      <p>Scroll down a bit to see it appear.</p>

      <div style={{ marginTop: '50vh' }}>
        <h2>Button should be visible now</h2>
      </div>
    </div>

    <button
      type="button"
      className="w-scroll-top-button"
      data-controller="w-scroll-top"
      data-w-scroll-top-threshold-value="100"
      data-action="click->w-scroll-top#scrollToTop"
      aria-label="Scroll to top"
      hidden
    >
      <svg className="w-scroll-top-icon" aria-hidden="true">
        <use href="#icon-arrow-up" />
      </svg>
    </button>
  </div>
);

export const CustomThreshold = CustomThresholdTemplate.bind({});
CustomThreshold.parameters = {
  docs: {
    description: {
      story:
        'You can customize when the button appears by changing the threshold value. This example shows a button that appears after scrolling 100px.',
    },
  },
};
