import { test, expect } from '@playwright/test';

test.describe('Chess Game', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('loads the game board correctly', async ({ page }) => {
        await expect(page.locator('[data-testid="chessboard"]')).toBeVisible();
        await expect(page.getByText('Chess Bot Arena')).toBeVisible();
    });

    test('starts a new game against bot', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        await expect(page.getByText('Human vs Bot')).toBeVisible();
        await expect(page.getByText('10:00')).toBeVisible();
    });

    test('handles invalid moves', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Try invalid pawn move
        await page.locator('[data-square="e2"]').click();
        await page.locator('[data-square="e6"]').click();
        
        await expect(page.getByText('Invalid move')).toBeVisible();
    });

    test('makes valid moves', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Make valid pawn move
        await page.locator('[data-square="e2"]').click();
        await page.locator('[data-square="e4"]').click();
        
        // Wait for bot response
        await expect(page.getByText('PROCESSING...')).toBeVisible();
        await expect(page.getByText('Last Move: e2e4')).toBeVisible();
    });

    test('handles network disconnection', async ({ page, context }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Simulate offline mode
        await context.setOffline(true);
        
        // Try to make a move
        await page.locator('[data-square="e2"]').click();
        await page.locator('[data-square="e4"]').click();
        
        await expect(page.getByText('Connection Lost')).toBeVisible();
        
        // Restore connection
        await context.setOffline(false);
        await expect(page.getByText('Reconnected')).toBeVisible();
    });

    test('handles game completion', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Play Against Bot').click();
        
        // Simulate checkmate sequence
        const moves = [
            ['f2', 'f3'],
            ['e7', 'e5'],
            ['g2', 'g4'],
            ['d8', 'h4']
        ];
        
        for (const [from, to] of moves) {
            await page.locator(`[data-square="${from}"]`).click();
            await page.locator(`[data-square="${to}"]`).click();
            // Wait for move to complete
            await page.waitForTimeout(1000);
        }
        
        await expect(page.getByText('Game Over')).toBeVisible();
        await expect(page.getByText('Checkmate')).toBeVisible();
    });

    test('changes game mode', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Watch Bots Play').click();
        
        await expect(page.getByText('Bot vs Bot')).toBeVisible();
        // Verify both timers are running
        await expect(page.getByText('9:59')).toHaveCount(2);
    });

    test('adjusts engine depth', async ({ page }) => {
        await page.getByRole('button', { name: 'New Game' }).click();
        await page.getByText('Advanced Settings').click();
        
        // Change depth for white
        await page.getByLabel('White Bot Depth').fill('4');
        await expect(page.getByText('White Bot Depth: 4')).toBeVisible();
        
        // Start game and verify depth is applied
        await page.getByText('Start Game').click();
        await expect(page.getByText('Depth: 4')).toBeVisible();
    });

    test('handles theme switching', async ({ page }) => {
        // Toggle theme
        await page.getByRole('button', { name: /toggle/i }).click();
        
        // Verify dark mode is applied
        await expect(page.locator('body')).toHaveClass(/chakra-ui-dark/);
        
        // Toggle back
        await page.getByRole('button', { name: /toggle/i }).click();
        await expect(page.locator('body')).toHaveClass(/chakra-ui-light/);
    });
}); 