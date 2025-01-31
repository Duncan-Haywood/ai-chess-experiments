/// <reference types="cypress" />

describe('Chess Game', () => {
  beforeEach(() => {
    cy.visit('/');
    // Wait for the board to be ready
    cy.get('.chess-board').should('be.visible');
  });

  it('should make a valid move', () => {
    // Click e2 pawn
    cy.get('[data-square="e2"]').click();
    
    // Verify square is highlighted
    cy.get('[data-square="e2"]').should('have.class', 'highlighted');
    
    // Click e4 square
    cy.get('[data-square="e4"]').click();
    
    // Verify the move was made
    cy.get('[data-square="e4"]')
      .find('.piece')
      .should('have.attr', 'data-piece')
      .and('include', 'wP');
    
    // Wait for bot response
    cy.get('.move-indicator', { timeout: 10000 })
      .should('not.have.class', 'loading');
  });

  it('should handle invalid moves correctly', () => {
    // Try to move a pawn diagonally without capture
    cy.get('[data-square="e2"]').click();
    cy.get('[data-square="f3"]').click();
    
    // Verify the pawn is still at e2
    cy.get('[data-square="e2"]')
      .find('.piece')
      .should('have.attr', 'data-piece')
      .and('include', 'wP');
  });

  it('should show game status correctly', () => {
    // Verify initial game status
    cy.get('.game-status').should('contain', 'ACTIVE');
    
    // Make some moves to reach checkmate (fool's mate)
    cy.get('[data-square="f2"]').click();
    cy.get('[data-square="f3"]').click();
    
    cy.get('[data-square="e7"]').click();
    cy.get('[data-square="e5"]').click();
    
    cy.get('[data-square="g2"]').click();
    cy.get('[data-square="g4"]').click();
    
    cy.get('[data-square="d8"]').click();
    cy.get('[data-square="h4"]').click();
    
    // Verify checkmate status
    cy.get('.game-status').should('contain', 'CHECKMATE');
  });

  it('should handle bot moves correctly', () => {
    // Make a move and verify bot responds
    cy.get('[data-square="e2"]').click();
    cy.get('[data-square="e4"]').click();
    
    // Wait for bot move
    cy.get('.move-indicator', { timeout: 10000 })
      .should('not.have.class', 'loading');
    
    // Verify that bot made a move (board state changed)
    cy.get('.last-move')
      .should('exist');
  });

  it('should show move history', () => {
    // Make a move
    cy.get('[data-square="e2"]').click();
    cy.get('[data-square="e4"]').click();
    
    // Verify move appears in history
    cy.get('.move-history')
      .should('contain', 'e2e4');
  });

  it('should handle time controls', () => {
    // Verify time is counting down
    cy.get('.white-time').invoke('text').then((initialTime) => {
      cy.wait(2000);
      cy.get('.white-time').invoke('text').should('not.eq', initialTime);
    });
  });
}); 