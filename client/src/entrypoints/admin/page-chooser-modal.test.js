import $ from 'jquery';
import './page-chooser-modal';

describe('page chooser anchors', () => {
  let modal;
  const render = (withAnchor = true) => {
    document.body.innerHTML = `
      <div id="modal">
        <form class="search-form" action="/admin/choose-page/search/">
          <input id="id_q" name="q">
        </form>
        ${withAnchor ? '<input name="page-link-chooser-anchor" value="initial">' : ''}
        <div class="page-results">
          <a class="choose-page" href="#3" data-id="3" data-url="/events/">Events</a>
        </div>
      </div>`;
  };

  beforeEach(() => {
    render();
    modal = {
      body: document.getElementById('modal'),
      ajaxifyForm: jest.fn(),
      respond: jest.fn(),
      close: jest.fn(),
    };
  });

  it('includes the optional anchor when choosing a page', () => {
    window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.browse(modal, {
      parent_page_id: 2,
    });
    const input = document.querySelector('[name="page-link-chooser-anchor"]');
    input.value = ' #contact ';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    document.querySelector('.choose-page').click();
    expect(modal.respond).toHaveBeenCalledWith('pageChosen', {
      id: 3,
      url: '/events/',
      parentId: 2,
      anchor: 'contact',
    });
    expect(modal.close).toHaveBeenCalled();
  });

  it('retains an edited anchor when browsing into a different parent', () => {
    window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.browse(modal, {
      parent_page_id: 2,
    });
    const input = document.querySelector('[name="page-link-chooser-anchor"]');
    input.value = 'contact';
    input.dispatchEvent(new Event('input', { bubbles: true }));
    render();
    modal.body = document.getElementById('modal');
    window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.browse(modal, {
      parent_page_id: 3,
    });
    expect(
      document.querySelector('[name="page-link-chooser-anchor"]').value,
    ).toBe('contact');
  });

  it('includes the anchor when choosing a search result', () => {
    jest.useFakeTimers();
    const ajax = jest.spyOn($, 'ajax').mockImplementationOnce(({ success }) => {
      success(
        '<a class="choose-page" href="#3" data-id="3" data-parent-id="2" data-url="/events/">Events</a>',
      );
      return {};
    });
    try {
      window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.browse(modal, {
        parent_page_id: 2,
      });
      const input = document.querySelector('[name="page-link-chooser-anchor"]');
      input.value = 'contact';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      const search = document.getElementById('id_q');
      search.value = 'Events';
      search.dispatchEvent(new Event('input', { bubbles: true }));
      jest.advanceTimersByTime(200);
      document.querySelector('.choose-page').click();
      expect(modal.respond).toHaveBeenCalledWith('pageChosen', {
        id: 3,
        parentId: 2,
        url: '/events/',
        anchor: 'contact',
      });
    } finally {
      ajax.mockRestore();
      jest.useRealTimers();
    }
  });

  it('leaves ordinary page choosers unchanged', () => {
    render(false);
    modal.body = document.getElementById('modal');
    window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.browse(modal, {
      parent_page_id: 2,
    });
    document.querySelector('.choose-page').click();
    expect(modal.respond).toHaveBeenCalledWith('pageChosen', {
      id: 3,
      url: '/events/',
      parentId: 2,
    });
  });
});

describe('external link conversion confirmation', () => {
  const data = {
    internal: { id: 3, parentId: 2, url: '/events/', anchor: 'section-3' },
    external: { url: 'http://localhost/events/#section-3' },
  };
  let modal;

  beforeEach(() => {
    document.body.innerHTML = `
      <div id="confirmation">
        <button type="button" data-action-confirm>Convert to internal link</button>
        <button type="button" data-action-deny>Use external link</button>
      </div>`;
    modal = {
      body: document.getElementById('confirmation'),
      respond: jest.fn(),
      close: jest.fn(),
    };
    window.PAGE_CHOOSER_MODAL_ONLOAD_HANDLERS.confirm_external_to_internal(
      modal,
      data,
    );
  });

  it('preserves the anchor when conversion is accepted', () => {
    document.querySelector('[data-action-confirm]').click();
    expect(modal.respond).toHaveBeenCalledWith('pageChosen', data.internal);
    expect(modal.close).toHaveBeenCalled();
  });

  it('preserves the original URL when conversion is declined', () => {
    document.querySelector('[data-action-deny]').click();
    expect(modal.respond).toHaveBeenCalledWith('pageChosen', data.external);
    expect(modal.close).toHaveBeenCalled();
  });
});
