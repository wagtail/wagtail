import 'cypress';
describe('Dropdown Action Component Accessibility', () => {
  beforeEach(() => {

    cy.visit('http://127.0.0.1:8000/admin/pages/3/');
    cy.get('#id_username').type('amanda');
    cy.get('#id_password').type('amanda123');
    cy.get('button[type="submit"]').click();

    cy.wait(500); 
  });


  it('should display the button', () => {
    cy.get('.w-dropdown__toggle-icon').invoke('show').should('be.visible')
    cy.get('.w-dropdown__toggle-icon').first().within(()  => {});
    cy.wait(500);
  })

  it('Página em forced-colors botão tem borda', () => {
  
    //ativa o modo forced-colors
    cy.get('body').invoke('attr', 'style', 'forced-colors: active');
  
    //verifica se o botão tem uma borda
    cy.get('.w-dropdown__toggle-icon').should('have.css', 'border', '0px solid rgb(255, 255, 255)');
  
  });
})






  // it('should have no accessibility violations with forced colors', () => {
  //   //Ativar o modo forced-colors
  //   cy.get('body').invoke('addClass', 'forced-colors');
    
  //   // Verifique a acessibilidade com cores forçadas
  //   cy.injectAxe();
  //   cy.checkA11y('.w-dropdown__toggle');
  // });  