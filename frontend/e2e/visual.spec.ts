import { test, expect } from '@playwright/test';

// Common test actions
const startGame = async (page) => {
    await page.getByRole('button', { name: 'New Game' }).click();
    await page.getByText('Play Against Bot').click();
};

const makeMove = async (page, from: string, to: string) => {
    await page.locator(`[data-square="${from}"]`).click();
    await page.locator(`[data-square="${to}"]`).click();
};

test.describe('Visual Regression', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
        // Ensure consistent viewport for snapshots
        await page.setViewportSize({ width: 1280, height: 720 });
    });

    test('game states match snapshots', async ({ page }) => {
        // Initial state
        await expect(page).toHaveScreenshot('initial-state.png', {
            mask: [page.locator('time')] // Mask dynamic time elements
        });

        // Game board
        await startGame(page);
        await expect(page.locator('[data-testid="chessboard"]')).toHaveScreenshot('game-board.png');

        // Move highlights
        await page.locator('[data-square="e2"]').click();
        await expect(page.locator('[data-testid="chessboard"]')).toHaveScreenshot('move-highlights.png');

        // After move
        await page.locator('[data-square="e4"]').click();
        await expect(page.locator('[data-testid="chessboard"]')).toHaveScreenshot('after-move.png');
    });

    test('theme variations', async ({ page }) => {
        // Light mode (default)
        await startGame(page);
        await expect(page).toHaveScreenshot('light-mode.png', {
            mask: [page.locator('time')]
        });

        // Dark mode
        await page.getByRole('button', { name: /toggle/i }).click();
        await expect(page).toHaveScreenshot('dark-mode.png', {
            mask: [page.locator('time')]
        });
    });

    test('responsive layouts', async ({ page }) => {
        const viewports = [
            { width: 1280, height: 720, name: 'desktop' },
            { width: 768, height: 1024, name: 'tablet' },
            { width: 375, height: 667, name: 'mobile' }
        ];

        for (const viewport of viewports) {
            await page.setViewportSize(viewport);
            await expect(page).toHaveScreenshot(`${viewport.name}-layout.png`, {
                mask: [page.locator('time')]
            });
        }
    });

    test('interactive elements', async ({ page }) => {
        // Modal
        await page.getByRole('button', { name: 'New Game' }).click();
        await expect(page.locator('[role="dialog"]')).toHaveScreenshot('game-modal.png');

        // Toast notification
        await startGame(page);
        await makeMove(page, 'e2', 'e6'); // Invalid move
        await expect(page.locator('[role="alert"]')).toHaveScreenshot('error-toast.png');

        // Game controls
        await expect(page.locator('.controls-container')).toHaveScreenshot('game-controls.png');
    });
}); 