import './telepath/telepath';
import './page-chooser-telepath';

describe('telepath: wagtail.widgets.PageChooser', () => {
  let boundWidget;

  beforeEach(() => {
    // Create a placeholder to render the widget
    document.body.innerHTML = '<div id="placeholder"></div>';

    const widgetDef = window.telepath.unpack({
      _type: 'wagtail.widgets.PageChooser',
      // Copy of wagtailadmin/widgets/chooser.html without verbose markup. Make sure to update when making changes to the template.
      _args: [
        `<div id="__ID__-chooser" class="chooser page-chooser blank" data-chooser-url="/admin/choose-page/">
          <div class="chosen">
            <div class="chooser__preview" role="presentation"></div>
            <div class="chooser__title" data-chooser-title id="__ID__-title"></div>
            <div data-controller="w-dropdown">
              <button
                type="button"
                class="w-dropdown__toggle"
                data-w-dropdown-target="toggle"
                aria-label="Actions"
                aria-describedby="__ID__-title"
              >
                dots-horizontal
              </button>
              <div class="w-dropdown__content" data-w-dropdown-target="content" hidden>
                <button type="button" data-chooser-action-choose aria-describedby="__ID__-title">
                  Choose another page
                </button>
                <a
                  href=""
                  data-chooser-edit-link
                  target="_blank"
                  rel="noreferrer"
                  aria-describedby="__ID__-title"
                >
                  Edit this page
                </a>
              </div>
            </div>
          </div>
          <div class="unchosen">
            <button type="button" data-chooser-action-choose class="button button-small button-secondary chooser__choose-button">
              Choose a page
            </button>
          </div>
        </div>
        <input type="hidden" name="__NAME__" id="__ID__">`,
        '__ID__',
        {
          modalUrl: '/admin/choose-page/',
          modelNames: ['wagtailcore.page'],
          canChooseRoot: false,
          userPerms: null,
        },
      ],
    });
    boundWidget = widgetDef.render(
      document.getElementById('placeholder'),
      'the-name',
      'the-id',
      {
        id: 60,
        parentId: 1,
        adminTitle: 'Welcome to the Wagtail Bakery!',
        editUrl: '/admin/pages/60/edit/',
      },
    );
  });

  test('it renders correctly', () => {
    expect(document.body.innerHTML).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('60');
  });

  test('getValue() returns the current value', () => {
    expect(boundWidget.getValue()).toBe(60);
  });

  test('getState() returns the current state', () => {
    expect(boundWidget.getState()).toEqual({
      id: 60,
      parentId: 1,
      adminTitle: 'Welcome to the Wagtail Bakery!',
      editUrl: '/admin/pages/60/edit/',
    });
  });

  test('setState() changes the current page', () => {
    boundWidget.setState({
      id: 34,
      parentId: 3,
      adminTitle: 'Anadama',
      editUrl: '/admin/pages/34/edit/',
    });
    expect(
      document.querySelector('[data-chooser-edit-link]'),
    ).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('34');
  });

  test('setState() to null clears the fields', () => {
    boundWidget.setState(null);
    expect(
      document.querySelector('[data-chooser-edit-link]'),
    ).toMatchSnapshot();
    expect(document.querySelector('input').value).toBe('');
  });

  test('focus() focuses the toggle button when widget is populated', () => {
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('.chooser button'),
    );
  });
  test('focus() focuses the toggle button when widget is blank', () => {
    boundWidget.setState(null);
    boundWidget.focus();

    expect(document.activeElement).toBe(
      document.querySelector('.chooser button'),
    );
  });
});
