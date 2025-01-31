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

test.describe('Stress Tests', () => {
    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('handles rapid game restarts', async ({ page }) => {
        // Start and immediately restart games rapidly
        for (let i = 0; i < 10; i++) {
            await startGame(page);
            await expect(page.locator('[data-testid="chessboard"]')).toBeVisible();
        }

        // Verify the game is still in a valid state
        await makeMove(page, 'e2', 'e4');
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles multiple concurrent moves', async ({ page }) => {
        await startGame(page);
        
        // Try to make moves without waiting for responses
        const moves = [
            ['e2', 'e4'],
            ['d2', 'd4'],
            ['c2', 'c4'],
            ['f2', 'f4']
        ];

        // Make moves concurrently
        await Promise.all(moves.map(([from, to]) => makeMove(page, from, to)));

        // Only one move should be processed
        const lastMoves = await page.locator('[data-testid="last-move"]').all();
        expect(lastMoves.length).toBe(1);
    });

    test('handles rapid theme switching', async ({ page }) => {
        await startGame(page);
        
        // Switch theme rapidly
        const themeToggle = page.getByRole('button', { name: /toggle/i });
        for (let i = 0; i < 20; i++) {
            await themeToggle.click();
        }

        // UI should still be responsive
        await makeMove(page, 'e2', 'e4');
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles network latency', async ({ page }) => {
        // Simulate slow network
        await page.route('**/*', async route => {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
            await route.continue();
        });

        await startGame(page);
        await makeMove(page, 'e2', 'e4');

        // Should show loading state
        await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
        // Should eventually complete the move
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles memory pressure', async ({ page, browserName }) => {
        test.skip(browserName !== 'chromium', 'Memory test only available in Chrome');
        
        await startGame(page);

        // Create memory pressure
        await page.evaluate(() => {
            const arrays: number[][] = [];
            for (let i = 0; i < 1000; i++) {
                arrays.push(new Array(10000).fill(0));
            }
            return arrays.length; // Keep reference to prevent GC
        });

        // Game should still be playable
        await makeMove(page, 'e2', 'e4');
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles rapid window resizing', async ({ page }) => {
        await startGame(page);

        const viewports = [
            { width: 1280, height: 720 },
            { width: 768, height: 1024 },
            { width: 375, height: 667 }
        ];

        // Rapidly change viewport sizes
        for (let i = 0; i < 10; i++) {
            for (const viewport of viewports) {
                await page.setViewportSize(viewport);
                // Verify board is still visible and interactive
                await expect(page.locator('[data-testid="chessboard"]')).toBeVisible();
            }
        }

        // Should still be able to play
        await makeMove(page, 'e2', 'e4');
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles long game sessions', async ({ page }) => {
        await startGame(page);
        
        // Play many moves
        const moves = [
            ['e2', 'e4'], ['e7', 'e5'],
            ['g1', 'f3'], ['b8', 'c6'],
            ['f1', 'b5'], ['a7', 'a6']
        ];

        // Play the sequence multiple times
        for (let i = 0; i < 5; i++) {
            for (const [from, to] of moves) {
                await makeMove(page, from, to);
                await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
            }
            await startGame(page); // Start new game
        }

        // Verify final game is in valid state
        await makeMove(page, 'e2', 'e4');
        await expect(page.locator('[data-testid="last-move"]')).toBeVisible();
    });

    test('handles rapid API requests', async ({ page }) => {
        await startGame(page);
        
        // Track failed requests
        let failedRequests = 0;
        page.on('requestfailed', () => failedRequests++);

        // Make many concurrent API calls
        const promises = [];
        for (let i = 0; i < 20; i++) {
            promises.push(
                page.evaluate(() => 
                    fetch('/api/game').catch(() => null)
                )
            );
        }

        await Promise.all(promises);
        expect(failedRequests).toBe(0);
    });
}); 