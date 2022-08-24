import React from 'react';

export default {
  title: 'Shared / Buttons',
};

const Template = ({ url }) => (
  <section id="buttons">
    <h2>Buttons</h2>

    <h3>Basic buttons</h3>
    <a href={url} className="button">
      button link
    </a>
    <button type="button" className="button">
      button element
    </button>

    <h3>Secondary buttons</h3>
    <a href={url} className="button button-secondary">
      button link
    </a>
    <button type="button" className="button button-secondary">
      button element
    </button>

    <h3>Small buttons</h3>
    <a href={url} className="button button-small">
      button link
    </a>
    <button type="button" className="button button-small">
      button element
    </button>

    <h4>Secondary buttons</h4>
    <a href={url} className="button button-small button-secondary">
      button link
    </a>
    <button type="button" className="button button-small button-secondary">
      button element
    </button>

    <h3>Disabled buttons</h3>
    <a href={url} className="button disabled">
      button link
    </a>
    <button type="button" className="button button-small disabled">
      button element
    </button>

    <h3>Bi-color icon buttons with text</h3>
    <a href={url} className="button bicolor button--icon">
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button link
    </a>
    <button type="button" className="button bicolor button--icon">
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button element
    </button>

    <h4>(small)</h4>
    <a href={url} className="button button-small bicolor button--icon">
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button link
    </a>
    <button type="button" className="button button-small bicolor button--icon">
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button element
    </button>

    <h3>Icon buttons without text</h3>
    <a href={url} className="button text-replace button--icon">
      <svg className="icon icon-cog icon" aria-hidden="true">
        <use href="#icon-cog" />
      </svg>
      button link
    </a>
    <button type="button" className="button text-replace button--icon">
      <svg className="icon icon-cog icon" aria-hidden="true">
        <use href="#icon-cog" />
      </svg>
      button element
    </button>

    <h4>(small)</h4>
    <a href={url} className="button button-small text-replace button--icon">
      <svg className="icon icon-cog icon" aria-hidden="true">
        <use href="#icon-cog" />
      </svg>
      button link
    </a>
    <button
      type="button"
      className="button button-small text-replace button--icon"
    >
      <svg className="icon icon-cog icon" aria-hidden="true">
        <use href="#icon-cog" />
      </svg>
      button element
    </button>

    <h3>Colour signifiers</h3>

    <h4>Positive</h4>
    <a href={url} className="button yes">
      yes
    </a>
    <a href={url} className="button button-small yes">
      yes
    </a>

    <h4>Negative</h4>
    <a href={url} className="button no">
      No
    </a>
    <a href={url} className="button button-small no">
      No
    </a>

    <h3>
      Buttons with internal loading indicators (currently only{' '}
      <code>button</code> supported)
    </h3>
    <button type="button" className="button button-longrunning">
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me
    </button>

    <h4>Secondary</h4>
    <button
      type="button"
      className="button button-secondary button-longrunning"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me
    </button>

    <h4>Small</h4>
    <button type="button" className="button button-small button-longrunning">
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me
    </button>

    <h4>Buttons where the text is replaced on click</h4>
    <button
      type="button"
      className="button button-longrunning"
      data-clicked-text="Test"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      <em>Click me</em>
    </button>
    <button
      type="button"
      className="button disabled button-longrunning--active"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      <span>Test</span>
    </button>

    <h3>Mixtures</h3>
    <a href={url} className="button button--icon text-replace white">
      <svg className="icon icon-cog icon" aria-hidden="true">
        <use href="#icon-cog" />
      </svg>
      A link button
    </a>
    <a href={url} className="button button--icon bicolor disabled">
      <span className="icon-wrapper">
        <svg className="icon icon-tick icon" aria-hidden="true">
          <use href="#icon-tick" />
        </svg>
      </span>
      button link
    </a>
  </section>
);

export const All = Template.bind({});

All.args = { url: window.location.toString() };
