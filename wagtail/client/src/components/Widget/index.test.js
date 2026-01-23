import { Widget, CheckboxInput, RadioSelect, Select } from './index';

describe('Widget', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = new Widget(
      '<input type="text" name="__NAME__" maxlength="255" id="__ID__">',
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id">',
    );
    expect(document.querySelector('input').value).toBe('The Value');
  });

  test('it fails rendering if no input is found', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    const nonWidget = new Widget('<div>Not an input</div>');
    expect(() => {
      nonWidget.render(
        document.getElementById('placeholder'),
        'the-name',
        'the-id',
        'The Value',
      );
    }).toThrow('No input found with name "the-name"');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('The Value');
    document.querySelector('input').value = 'New Value';
    expect(boundWidget.getValue()).toBe('New Value');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe('The Value');
    document.querySelector('input').value = 'New Value';
    expect(boundWidget.getState()).toBe('New Value');
  });

  test('setState() changes the current state', () => {
    boundWidget.setState('The new Value');
    expect(document.querySelector('input').value).toBe('The new Value');
  });

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(document.querySelector('input').getAttribute('aria-invalid')).toBe(
      'true',
    );
    boundWidget.setInvalid(false);
    expect(
      document.querySelector('input').getAttribute('aria-invalid'),
    ).toBeNull();
  });

  test('getTextLabel() returns a truncated text label', () => {
    expect(boundWidget.getTextLabel()).toBe('The Value');
    expect(boundWidget.getTextLabel({ maxLength: 6 })).toBe('The V…');
  });

  test('focus() focuses the text input', () => {
    boundWidget.focus();
    expect(document.activeElement).toBe(document.querySelector('input'));
  });

  test('it should support options with attributes', () => {
    document.body.innerHTML = '<div id="placeholder"></div>';
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
      {},
      {
        attributes: {
          'maxLength': 512,
          'aria-describedby': 'some-id',
          'required': '',
        },
      },
    );

    const input = document.querySelector('input');

    expect(input.maxLength).toBe(512);
    expect(input.getAttribute('aria-describedby')).toBe('some-id');
    expect(input.required).toBe(true);
  });

  it('can be retrieved for an existing form element', () => {
    document.body.innerHTML =
      '<input type="text" name="surname" id="id_surname" value="Bobson">';
    const otherBoundWidget = widgetDef.getByName('surname', document.body);
    expect(otherBoundWidget.getValue()).toBe('Bobson');
  });
});

describe('Widget with inline JS', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = new Widget(
      '<div><input type="text" name="__NAME__" maxlength="255" id="__ID__"><script>document.getElementById("__ID__").className = "custom-class";</script></div>',
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.querySelector('input').outerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id" class="custom-class">',
    );
    expect(document.querySelector('input').value).toBe('The Value');

    // boundWidget still acts on the input, despite it not being the top-level element
    boundWidget.setState('New Value');
    expect(document.querySelector('input').value).toBe('New Value');
  });
});

describe('Widget with multiple top-level nodes', () => {
  let boundWidget;
  let widgetDef;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    widgetDef = new Widget(
      '<!-- here comes a widget --><input type="text" name="__NAME__" maxlength="255" id="__ID__"><button data-button-state="idle">Click me</button><script>document.getElementById("__ID__").className = "custom-class";</script>',
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      'The Value',
    );
  });

  test('it renders correctly', () => {
    expect(document.body.querySelector('input').outerHTML).toBe(
      '<input type="text" name="the-name" maxlength="255" id="the-id" class="custom-class">',
    );
    expect(document.querySelector('[data-button-state]').outerHTML).toBe(
      '<button data-button-state="idle">Click me</button>',
    );
    expect(document.querySelector('input').value).toBe('The Value');
  });
});

describe('RadioSelect', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = new RadioSelect(
      `<ul id="__ID__">
        <li>
          <label for="__ID___0">
          <input type="radio" name="__NAME__" value="tea" id="__ID___0"> Tea</label>
        </li>
        <li>
          <label for="__ID___1">
          <input type="radio" name="__NAME__" value="coffee" id="__ID___1"> Coffee</label>
        </li>
      </ul>`,
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['tea'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[value="tea"]').checked).toBe(true);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(false);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('tea');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['tea']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['coffee']);
    expect(document.querySelector('input[value="tea"]').checked).toBe(false);
    expect(document.querySelector('input[value="coffee"]').checked).toBe(true);
  });

  test('setInvalid() sets aria-invalid attribute', () => {
    boundWidget.setInvalid(true);
    expect(
      document.querySelector('input[value="tea"]').getAttribute('aria-invalid'),
    ).toBe('true');
    expect(
      document
        .querySelector('input[value="coffee"]')
        .getAttribute('aria-invalid'),
    ).toBe('true');
    boundWidget.setInvalid(false);
    expect(
      document.querySelector('input[value="tea"]').getAttribute('aria-invalid'),
    ).toBeNull();
    expect(
      document
        .querySelector('input[value="coffee"]')
        .getAttribute('aria-invalid'),
    ).toBeNull();
  });

  test('getTextLabel() returns the text of selected option', () => {
    expect(boundWidget.getTextLabel()).toBe('Tea');
  });

  test('getTextLabel() safely handles input with no labels', () => {
    // Disassociate the label from the input by removing the "for" attribute
    // and moving the input outside of the label.
    const label = document.querySelector('label[for="the-id_0"]');
    label.removeAttribute('for');
    const input = document.querySelector('input[value="tea"]');
    document.body.appendChild(input);
    expect(boundWidget.getTextLabel()).toBe('');
  });

  test('focus() focuses the first element', () => {
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('input[value="tea"]'),
    );
  });
});

describe('RadioSelect for CheckboxSelectMultiple', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = new RadioSelect(
      `<ul id="__ID__">
        <li>
          <label for="__ID___0">
          <input type="checkbox" name="__NAME__" value="red" id="__ID___0"> Red</label>
        </li>
        <li>
          <label for="__ID___1">
          <input type="checkbox" name="__NAME__" value="green" id="__ID___1"> Green</label>
        </li>
        <li>
          <label for="__ID___2">
          <input type="checkbox" name="__NAME__" value="blue" id="__ID___2"> Blue</label>
        </li>
      </ul>`,
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['red', 'blue'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input[value="red"]').checked).toBe(true);
    expect(document.querySelector('input[value="green"]').checked).toBe(false);
    expect(document.querySelector('input[value="blue"]').checked).toBe(true);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toStrictEqual(['red', 'blue']);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['red', 'blue']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['red', 'green']);
    expect(document.querySelector('input[value="red"]').checked).toBe(true);
    expect(document.querySelector('input[value="green"]').checked).toBe(true);
    expect(document.querySelector('input[value="blue"]').checked).toBe(false);
  });

  test('getTextLabel() returns the text of selected options', () => {
    expect(boundWidget.getTextLabel()).toBe('Red, Blue');
  });

  test('getTextLabel() safely handles input with no labels', () => {
    // Disassociate the label from the input by removing the "for" attribute
    // and moving the input outside of the label.
    const label = document.querySelector('label[for="the-id_0"]');
    label.removeAttribute('for');
    const input = document.querySelector('input[value="red"]');
    document.body.appendChild(input);
    expect(boundWidget.getTextLabel()).toBe('Blue');
  });
});

describe('CheckboxInput', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = new CheckboxInput(
      '<input type="checkbox" name="__NAME__" id="__ID__">',
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'sugar',
      'id-sugar',
      true,
    );
  });

  test('it renders correctly', () => {
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(true);
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe(true);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toBe(true);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(false);
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(false);
    boundWidget.setState(true);
    expect(document.querySelector('input[id="id-sugar"]').checked).toBe(true);
  });

  test('getTextLabel() returns a human-readable value', () => {
    expect(boundWidget.getTextLabel()).toBe('Yes');
    boundWidget.setState(false);
    expect(boundWidget.getTextLabel()).toBe('No');
  });

  test('focus() focuses the checkbox', () => {
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('input[id="id-sugar"]'),
    );
  });
});

describe('Select', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = new Select(
      `<select name="__NAME__" id="__ID__">
        <option value="1">Option 1</option>
        <option value="2">Option 2</option>
      </select>`,
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['1'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    const select = document.querySelector('select');
    expect(select.options[select.selectedIndex].value).toBe('1');
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(1);
    expect(selectedOptions[0].value).toBe('1');
  });

  test('getTextLabel() returns the truncated text of selected option', () => {
    expect(boundWidget.getTextLabel()).toBe('Option 1');
    expect(boundWidget.getTextLabel({ maxLength: 6 })).toBe('Optio…');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe('1');
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['1']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['2']);
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(1);
    expect(selectedOptions[0].value).toBe('2');
  });
});

describe('Select multiple', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = new Select(
      `<select name="__NAME__" id="__ID__" multiple>
        <option value="red">Red</option>
        <option value="green">Green</option>
        <option value="blue">Blue</option>
      </select>`,
    );
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      ['red', 'blue'],
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    const select = document.querySelector('select');
    expect(select.options[select.selectedIndex].value).toBe('red');
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(2);
    expect(selectedOptions[0].value).toBe('red');
    expect(selectedOptions[1].value).toBe('blue');
  });

  test('getTextLabel() returns the truncated text of selected options', () => {
    expect(boundWidget.getTextLabel()).toBe('Red, Blue');
    expect(boundWidget.getTextLabel({ maxLength: 6 })).toBe('Red, …');
  });

  test('getValue() returns the current values', () => {
    expect(boundWidget.getValue()).toStrictEqual(['red', 'blue']);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toStrictEqual(['red', 'blue']);
  });

  test('setState() changes the current state', () => {
    boundWidget.setState(['red', 'green']);
    const selectedOptions = document.querySelector('select').selectedOptions;
    expect(selectedOptions.length).toBe(2);
    expect(selectedOptions[0].value).toBe('red');
    expect(selectedOptions[1].value).toBe('green');
  });
});
