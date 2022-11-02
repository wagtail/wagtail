import { initButtonSelects } from './initButtonSelects';

describe('initButtonSelects', () => {
  const spy = jest.spyOn(document, 'addEventListener');

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should do nothing if there is no button-select container', () => {
    // Set up our document body
    document.body.innerHTML = `
    <div>
      <input type="hidden" />
      <button class="button-select__option" />
    </div>`;
    initButtonSelects();
    // no event listeners registered
    expect(spy).not.toHaveBeenCalled();
});

describe('there is a button-select container present', () => {
  it('should add class of to button-select when clicked', ()=>{
    document.body.innerHTML=`
    <div class = "button-select">
      <input type="hidden" value />
      <button class="button-select__option">
        All
      </button>
      <button class="button-select__option">
        Awaiting my review
      </button>
    </div>
  
    <div class="button-select">
      <input type="hidden" value />
      <button class="button-select__option">
        All
      </button>
      <button class="button-select__option">
        In Progress
      </button>
      <button class="button-select__option">
        Approved
      </button>
      <button class="button-select__option">
        Needs changes
      </button>
      <button class="button-select__option">
        Cencelled
      </button>
    </div>
  `

  initButtonSelects();
  // event listeners registered
  expect(spy).toHaveBeenCalled();

  document.querySelectorAll(".button-select").forEach((buttonSelect)=>{
    buttonSelect.querySelectorAll(".button-select__option").forEach((button)=>{
      button.addEventListener("click", ()=>{
        expect(button.classList.contains).to('button-select__option--selected');
      });
    })
  })

})

})

  //   it('should collapse the breadcrumbs when clicked, if expanded', () => {
  //     // collapse the breadcrumbs
  //     document.getElementById('button').click();
  //     expect(
  //       document.getElementById('button').getAttribute('aria-expanded'),
  //     ).toBe('false');
  //     expect(document.getElementById('use').getAttribute('href')).toBe(
  //       '#icon-breadcrumb-expand',
  //     );
  //   });

  //   it('should use header based on data attribute', () => {
  //     document.body.innerHTML = `
  //     <div id="hover">
  //       <div data-breadcrumb-next data-header-selector="#hover">
  //         <button id="button" data-toggle-breadcrumbs>
  //           <svg aria-hidden="true">
  //             <use id="use" href="#icon-breadcrumb-expand" />
  //           </svg>
  //         </button>
  //         <nav aria-label="Breadcrumb">
  //           <span id="username" data-breadcrumb-item />
  //         </nav>
  //       </div>
  //     </div>`;

  //     expect(spy).not.toHaveBeenCalled();

  //     const containerSpy = jest.spyOn(
  //       document.getElementById('hover'),
  //       'addEventListener',
  //     );

  //     expect(containerSpy).not.toHaveBeenCalled();

  //     initCollapsibleBreadcrumbs();

  //     expect(spy).toHaveBeenLastCalledWith('keydown', expect.any(Function));
  //     expect(containerSpy).toHaveBeenLastCalledWith(
  //       'mouseleave',
  //       expect.any(Function),
  //     );
  //   });
  // });
});
