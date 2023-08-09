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

    <h4>
      Basic buttons <small>(small)</small>
    </h4>
    <a href={url} className="button button-small">
      button link
    </a>
    <button type="button" className="button button-small">
      button element
    </button>

    <h3>Secondary buttons</h3>
    <a href={url} className="button button-secondary">
      button link
    </a>
    <button type="button" className="button button-secondary">
      button element
    </button>

    <h4>
      Secondary buttons <small>(small)</small>
    </h4>
    <a href={url} className="button button-secondary button-small">
      button link
    </a>
    <button type="button" className="button button-secondary button-small">
      button element
    </button>

    <h3>Disabled buttons</h3>
    <p>
      <strong>Important</strong>: Adding <code>disabled</code> as a class should
      be avoided on buttons, instead use the disabled attribute. Some examples
      below use classes to validate existing styling still works.
    </p>

    <a href={url} className="button disabled">
      button link
    </a>
    <button type="button" className="button" disabled>
      button element
    </button>
    <button type="button" className="button button-secondary" disabled>
      button element
    </button>

    <h4>
      Disabled buttons <small>(small)</small>
    </h4>
    <a href={url} className="button button-small disabled">
      button link
    </a>
    <button type="button" className="button button-small disabled">
      button element
    </button>
    <button
      type="button"
      className="button button-small button-secondary"
      disabled
    >
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
    <button type="button" className="button bicolor button--icon" disabled>
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button disabled
    </button>

    <h4>Bi-color secondary icon buttons with text</h4>
    <a href={url} className="button bicolor button--icon button-secondary">
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button link
    </a>
    <button
      type="button"
      className="button bicolor button--icon button-secondary"
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button element
    </button>
    <button
      type="button"
      className="button bicolor button--icon button-secondary"
      disabled
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button disabled
    </button>

    <h4>
      Bi-color icon buttons with text <small>(small)</small>
    </h4>
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
    <button
      type="button"
      className="button button-small bicolor button--icon"
      disabled
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button disabled
    </button>

    <h4>
      Bi-color secondary icon buttons with text <small>(small)</small>
    </h4>
    <a
      href={url}
      className="button button-small bicolor button--icon button-secondary"
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button link
    </a>
    <button
      type="button"
      className="button button-small bicolor button--icon button-secondary"
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button element
    </button>
    <button
      type="button"
      className="button button-small bicolor button--icon button-secondary"
      disabled
    >
      <span className="icon-wrapper">
        <svg className="icon icon-plus icon" aria-hidden="true">
          <use href="#icon-plus" />
        </svg>
      </span>
      button disabled
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

    <h4>
      Icon buttons without text <small>(small)</small>
    </h4>
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

    <h3>Negative</h3>
    <a href={url} className="button no">
      No link
    </a>
    <button type="button" className="button no">
      No button
    </button>
    <button type="button" className="button no" disabled>
      No disabled
    </button>

    <h4>
      Negative <small>(small)</small>
    </h4>
    <p>
      Should not be used with <code>.button-secondary</code> on the same
      element.
    </p>
    <a href={url} className="button button-small no">
      No
    </a>
    <button type="button" className="button button-small no">
      No
    </button>
    <button type="button" className="button button-small no" disabled>
      Disabled
    </button>

    <h3>Buttons with internal loading indicators</h3>
    <p>
      Currently only <code>button</code> elements are supported.
    </p>

    <button
      type="button"
      className="button button-longrunning"
      data-controller="w-progress"
      data-action="w-progress#activate"
      data-w-progress-duration-value="5000"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me 5s
    </button>
    <button
      type="button"
      className="button button-secondary button-longrunning"
      data-controller="w-progress"
      data-action="w-progress#activate"
      data-w-progress-duration-value="5000"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me 5s
    </button>
    <button
      type="button"
      className="button button-small button-longrunning"
      data-controller="w-progress"
      data-action="w-progress#activate"
      data-w-progress-duration-value="5000"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      Click me 5s
    </button>

    <h4>Buttons where the text is replaced on click</h4>
    <button
      type="button"
      className="button button-longrunning"
      data-controller="w-progress"
      data-action="w-progress#activate"
      data-w-progress-duration-value="5000"
      data-w-progress-active-value="Test"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      <em data-w-progress-target="label">Click me</em>
    </button>
    <button
      type="button"
      className="button disabled button-longrunning--active"
      data-controller="w-progress"
      data-action="w-progress#activate"
      data-w-progress-duration-value="5000"
    >
      <svg className="icon icon-spinner icon" aria-hidden="true">
        <use href="#icon-spinner" />
      </svg>
      <span data-w-progress-target="label">Test</span>
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
        <svg className="icon icon-check icon" aria-hidden="true">
          <use href="#icon-check" />
        </svg>
      </span>
      button link
    </a>
  </section>
);

export const All = Template.bind({});

All.args = { url: window.location.toString() };
